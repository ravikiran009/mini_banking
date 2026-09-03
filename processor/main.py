from uuid import uuid4
from fastapi import FastAPI
from common.db import StoreSpannerExecutorSingleton
from common.logger import Logger
from common.utils import performancetracker

app = FastAPI()

@app.get("/")
@performancetracker
def health():
    return "Health Check Successful ✅"

@app.get("/api/user_id/{user_id}")
@performancetracker
def get_user(user_id: int):
    log = Logger(trace_id=str(uuid4()), operation="GetUser")
    try:
        spanner_executor = StoreSpannerExecutorSingleton(log)
        _usr = next(spanner_executor.user(user_id), None)
        if not _usr:
            return {}
        return _usr.model_dump(by_alias=True, exclude_none=True)
    except Exception as exc:
        log.error(f"Failed to fetch user {user_id}: {exc}")
        return "An unexpected error occured. Please try again later"

@app.get("/api/v2/user_id/{user_id}")
@performancetracker
def get_user_v2(user_id: int):
    log = Logger(trace_id=str(uuid4()), operation="GetUserV2")
    try:
        spanner_executor = StoreSpannerExecutorSingleton(log)
        _usr = next(spanner_executor.user_v2(user_id), None)
        if not _usr:
            return {}
        return _usr
    except Exception as exc:
        log.error(f"Failed to fetch user_v2 {user_id}: {exc}")
        return "An unexpected error occured. Please try again later"

@app.get("/api/transactions/{user_id}")
@performancetracker
def get_transactions(user_id: int, limit: int | None = None):
    log = Logger(trace_id=str(uuid4()), operation="GetTransactions")
    try:
        spanner_executor = StoreSpannerExecutorSingleton(log)
        return [item.model_dump(by_alias=True, exclude_none=True) for item in spanner_executor.transactions(user_id, limit)]
    except Exception as exc:
        log.error(f"Failed to fetch transactions for user {user_id}: {exc}")
        return "An unexpected error occured. Please try again later"

@app.get("/api/v2/transactions/{user_id}")
@performancetracker
def get_transactions_v2(user_id: int, limit: int | None = None):
    log = Logger(trace_id=str(uuid4()), operation="GetTransactionsV2")
    try:
        spanner_executor = StoreSpannerExecutorSingleton(log)
        return list(spanner_executor.transactions_v2(user_id, limit))
    except Exception as exc:
        log.error(f"Failed to fetch transactions_v2 for user {user_id}: {exc}")
        return "An unexpected error occured. Please try again later"

@app.post("/api/v1/process/")
@performancetracker
def process(data: dict|None = None):
    pass
