from uuid import uuid4
from fastapi import FastAPI
from processor.db import user, user_v2, transactions, transactions_v2
from common.logger import Logger

app = FastAPI()

@app.get("/")
def health():
    return "Health Check Successful ✅"


@app.get("/user_id/{user_id}")
def get_user(user_id:int):
    log = Logger(trace_id=str(uuid4()))
    try:
        _usr = next(user(log, user_id),None)
        if not _usr:
            return {}
        return _usr.model_dump(by_alias=True, exclude_none=True)
    except:
        return "An unexpected error occured. Please try again later"


@app.get("/v2/user_id/{user_id}")
def get_user_v2(user_id:int):
    log = Logger(trace_id=str(uuid4()))
    try:
        _usr = next(user_v2(log, user_id),None)
        if not _usr:
            return {}
        return _usr
    except:
        return "An unexpected error occured. Please try again later"


@app.get("/transactions/{user_id}")
def get_transactions(user_id:int, limit:int|None=None):
    log = Logger(trace_id=str(uuid4()))
    try:
        return [item.model_dump(by_alias=True, exclude_none=True) for item in transactions(log, user_id, limit)]
    except:
        return "An unexpected error occured. Please try again later"


@app.get("/v2/transactions/{user_id}")
def get_transactions_v2(user_id:int, limit:int|None=None):
    log = Logger(trace_id=str(uuid4()))
    try:
        return list(transactions_v2(log, user_id, limit))
    except:
        return "An unexpected error occured. Please try again later"