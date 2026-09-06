import json
import requests
from dataclasses import dataclass, field

from common.logger import Logger
from common.responses import SuccessResponse, FailureResponse

@dataclass(slots=True)
class ExternalRequestHandler:
    logger: Logger = field(default_factory=lambda: Logger(operation="ExternalEventHandler"))

    def post(self, url: str, data: dict | None = None):
        if data is None:
            data = {}
        try:
            resp = requests.post(
                url=url, 
                data=json.dumps(data, default=str),
                headers = {"Content-Type": "application/json"}
                )
            resp.raise_for_status()  # Raises HTTPError for 4xx/5xx status codes (e.g., 404 Not Found)
            self.logger.info(f"Post to {url} successful with data: {data}", operation="ExternalEventHandler")
            return SuccessResponse(msg="Post Successful")
        except Exception as exc:
            self.logger.error(f"Failed to post to url '{url}': {exc}", operation="ExternalEventHandler")
            return FailureResponse(msg=exc)