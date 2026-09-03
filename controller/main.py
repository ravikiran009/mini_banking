import pandas as pd
from uuid import uuid4
from dataclasses import dataclass, field
from datetime import datetime

from common.logger import Logger
from common.config import config, Config
from common.db import StagingSpannerExecutorPool
from common.requests import ExternalRequestHandler


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
            self.external_request_handler.post(url=self.config.processor_url, data=event)

    # Fetch staged events
    def consume_events(self):
        stg_pool = StagingSpannerExecutorPool(self.logger)

        for events in stg_pool.get_transaction_events():
            self.batch_process_events(events)
