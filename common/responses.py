"""Custom responses for mini-banking system"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class SuccessResponse:
    msg: str = field(default="Request submission Successful")
    resp: dict = field(default=lambda: dict({"status":"succesful"}))
    status_code: int = field(default=200)


@dataclass(slots=True)
class FailureResponse:
    msg: str = field(default="Request submission Failed")
    status_code: int = field(default=400)


@dataclass(slots=True)
class ActionNotRequired:
    msg: str = field(default="No need to process this request")
    status_code: int = field(default=204)