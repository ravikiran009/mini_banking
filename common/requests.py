import json

import requests
from requests import Session
from dataclasses import dataclass, field

from common.logger import Logger
from common.responses import SuccessResponse, FailureResponse
from common.utils import get_session, close_session

@dataclass(slots=True)
class ExternalRequestHandler:
    logger: Logger = field(default_factory=lambda: Logger(operation="ExternalEventHandler"))
    session: Session = field(default_factory=get_session)

    def post(self, url: str, data: dict | None = None):
        if data is None:
            data = {}
        try:
            resp = self.session.post(
                url=url,
                data=json.dumps(data, default=str),
                headers={"Content-Type": "application/json"}
            )
            resp.raise_for_status()  # Raises HTTPError for 4xx/5xx status codes
            self.logger.info(f"Post to {url} successful with data: {data}", operation="ExternalEventHandler")
            return SuccessResponse(msg="Post Successful")
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as exc:
            # Auto-heal: Broken/corrupted socket. Discard and refresh singleton session.
            self.logger.error(f"Connection corrupted on '{url}', resetting session: {exc}", operation="ExternalEventHandler")
            close_session()
            self.session = get_session()
            return FailureResponse(msg=exc)
        except Exception as exc:
            self.logger.error(f"Failed to post to url '{url}': {exc}", operation="ExternalEventHandler")
            return FailureResponse(msg=exc)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and issubclass(exc_type, (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError)):
            close_session()