import os
import pandas as pd
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime

from common.logger import Logger
from common.config import config, Config
from common.db import StagingSpannerExecutorPool, BATCH_SIZE
from common.requests import ExternalRequestHandler
from common.responses import SuccessResponse, FailureResponse


@dataclass(slots=True)
class EventsProcessor:
    logger: Logger
    external_request_handler: ExternalRequestHandler
    staging_db_executor: StagingSpannerExecutorPool
    config: Config
    max_workers: int = field(default_factory=lambda: int(os.getenv("CONTROLLER_MAX_WORKERS", "8")))

    # Format event fields for proper Json Serializing
    def _preprocess(self, event: dict):
        for key, value in event.items():
            if isinstance(value, datetime):
                event[key] = value.isoformat()
            elif value is None or (isinstance(value, float) and value != value):
                event[key] = None

    def _process_single_event(self, event: dict):
        self._preprocess(event)
        try:
            resp = self.external_request_handler.post(url=self.config.processor_url, data=event)
            if isinstance(resp, FailureResponse):
                self.logger.error(f"Failed to post event trace_id={event.get('trace_id')}: {resp.msg}")
                return resp
            return resp
        except Exception as exc:
            self.logger.error(f"Unable to process event trace_id={event.get('trace_id')}: {exc}")
            return FailureResponse(msg=f"Unable to post event: {exc}")

    def _process_user_events(self, user_events: list[dict]):
        for event in user_events:
            self._process_single_event(event)

    # Process staged events in batches concurrently with sequential execution per user
    def batch_process_events(self, events: pd.DataFrame, executor: ThreadPoolExecutor):
        records = events.to_dict(orient="records")
        if not records:
            return SuccessResponse(msg="BatchProcess events completed")

        # Group records by user_id so events for the same user are processed strictly in sequence
        user_events_map = defaultdict(list)
        for idx, record in enumerate(records):
            user_id = record.get("user_id")
            key = user_id if user_id is not None else f"__unassigned_{idx}__"
            user_events_map[key].append(record)

        futures = [
            executor.submit(self._process_user_events, user_records)
            for user_records in user_events_map.values()
        ]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                self.logger.error(f"Worker execution failed: {exc}")

        return SuccessResponse(msg="BatchProcess events completed")

    # Fetch staged events
    def consume_events(self):
        batches_processed = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for events in self.staging_db_executor.get_transaction_events():
                self.batch_process_events(events, executor=executor)
                batches_processed += 1
                if batches_processed % BATCH_SIZE == 0:
                    self.logger.info("Number of batches processed: ", batches_processed)

        self.logger.info("Number of batches processed: ", batches_processed)
