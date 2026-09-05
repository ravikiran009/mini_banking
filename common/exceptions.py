"""Custom exceptions for mini-banking system"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class InvalidTransactionEvent(Exception):
    msg: str = field(default="Invalid Transaction Event")


@dataclass(slots=True)
class InvalidSQLTransaction(Exception):
    msg: str = field(default="Invalid SQL transaction")