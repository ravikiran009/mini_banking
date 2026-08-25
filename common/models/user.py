from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

from dataclasses import dataclass


class User(BaseModel) : 
    model_config = ConfigDict(populate_by_name = True, extra = 'forbid')

    user_id : int = Field(alias = 'UserId')
    account_id : str = Field(alias = 'AccountId')
    balance : int = Field(alias = 'Balance')
    last_transaction_id : str | None = Field(default=None, alias = 'LastTransactionId')


@dataclass(slots=True)
class UserV2:
    user_id : int
    account_id : str
    balance : int
    last_transaction_id : str | None = None