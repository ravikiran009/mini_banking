import pandas as pd
from uuid import uuid4
from dataclasses import dataclass, field
from datetime import datetime

from common.logger import Logger
from common.config import config, Config
from common.db import StagingSpannerExecutorPool, BATCH_SIZE
from common.requests import ExternalRequestHandler
from common.responses import SuccessResponse, FailureResponse


@dataclass(slots=True)
class EventsProcessor:
    logger: Logger = field(default_factory=lambda: Logger(operation='EventsProcessor'))
    config: Config = field(default_factory=lambda: config)
    external_request_handler: ExternalRequestHandler = field(init=False)

    # Pass the same logger to ExternalRequestHandler that calls processor post endpoint
    def __post_init__(self):
        self.external_request_handler = ExternalRequestHandler(self.logger)

    # Format event fields for proper Json Serializing
    def _preprocess(self, event: dict):
        for key, value in event.items():
            if isinstance(value, datetime):
                event[key] = value.isoformat()
            elif pd.isna(value):
                event[key] = None

    # Process staged events in batches
    def batch_process_events(self, events: pd.DataFrame):
        for event in events.to_dict(orient="records"):
            self._preprocess(event)
            try:
                resp = self.external_request_handler.post(url=self.config.processor_url, data=event)
                if isinstance(resp, FailureResponse):
                    self.logger.error(f"Failed to post event trace_id={event.get('trace_id')}: {resp.msg}")
            except Exception as exc:
                self.logger.error(f"Unable to process event : {exc}")
                return FailureResponse(msg=f"Unable to post event: {exc}")
        return SuccessResponse(msg="BatchProcess events completed")

    # Fetch staged events
    def consume_events(self):
        stg_pool = StagingSpannerExecutorPool(self.logger)

        batches_processed = 0
        for events in stg_pool.get_transaction_events():
            self.batch_process_events(events)
            batches_processed += 1
            if batches_processed%BATCH_SIZE == 0:
                self.logger.info("Number of batches processed: ", batches_processed)
        
        self.logger.info("Number of batches processed: ", batches_processed)
