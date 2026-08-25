from datetime import datetime
from pydantic import BaseModel, Field, field_serializer
from pydantic.config import ConfigDict

from dataclasses import dataclass

class Transaction(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')

    user_id : int = Field(alias = 'UserId')
    transaction_id : str = Field(alias = 'TransactionId')
    transaction_type : str = Field(alias = 'TransactionType')
    amount : int = Field(alias = 'Amount')
    from_user : int | None = Field(default = None, alias = 'FromUser')
    transaction_timestamp : datetime = Field(alias = 'TransactionTimestamp')

    @field_serializer('transaction_timestamp')
    def format_timestamp(self, dt: datetime) -> str:
        return dt.isoformat(timespec='seconds').replace("+00:00", "Z")

@dataclass(slots=True)
class TransactionV2:
    user_id : int
    transaction_id : str
    transaction_type : str
    amount : int
    transaction_timestamp : datetime
    from_user : int | None = None

    def __post_init__(self):
        self.transaction_timestamp=self.transaction_timestamp.isoformat(timespec='seconds').replace('+00:00', 'Z')
