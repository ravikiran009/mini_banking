import os
from uuid import uuid4
from typing import TypeVar
from pydantic import BaseModel,ValidationError
from collections.abc import Iterator
from google.cloud import spanner
from google.cloud.spanner_v1.streamed import StreamedResultSet
from common.logger import Logger
from common.models.user import User, UserV2
from common.models.transaction import Transaction, TransactionV2


client=spanner.Client(project='mini-banking')
database_instance=client.instance(instance_id='store-db-instance')
database=database_instance.database(database_id='store-db')


def _yield_response_payload(logger:Logger,model_class:type[BaseModel],data:StreamedResultSet) -> Iterator[BaseModel]:
    # keys = model_class.model_fields.keys()
    # logger.debug(keys,check='Attrs')
    col_names = None
    for row in data:
        if not col_names:
            col_names = [field.name for field in data.fields]
        row_dict = dict(zip(col_names, row))
        # logger.debug(row_dict,check='Values')
        item = model_class.model_validate(row_dict)
        yield item


T = TypeVar('T')

def _yield_response_payload_v2(logger:Logger,model_class:type[T],data:StreamedResultSet) -> Iterator[T]:
    # keys = model_class.__slots__
    # logger.debug(keys,check='AttrsV2')
    col_names = None
    for row in data:
        if not col_names:
            col_names = [field.name for field in data.fields]
        row_dict = dict(zip(col_names, row))
        # logger.debug(row_dict,check='ValuesV2')
        item = model_class(**row_dict)
        yield item        


def user(log:Logger, user_id:int) -> Iterator[User]:
    sql="select * from users where user_id = @user_id"
    params={"user_id":user_id}
    param_types={"user_id":spanner.param_types.INT64}
    try:
        with database.snapshot() as db:
            results=db.execute_sql(sql=sql,params=params,param_types=param_types)
            yield from _yield_response_payload(log,User,results)
    except Exception as exc:
        log.error(f'Unable to retrieve data : {exc}', operation='FetchUser')
        raise


def user_v2(log:Logger, user_id:int) -> Iterator[UserV2]:
    sql="select * from users where user_id = @user_id"
    params={"user_id":user_id}
    param_types={"user_id":spanner.param_types.INT64}
    try:
        with database.snapshot() as db:
            results=db.execute_sql(sql=sql,params=params,param_types=param_types)
            yield from _yield_response_payload_v2(log,UserV2,results)
    except Exception as exc:
        log.error(f'Unable to retrieve data : {exc}', operation='FetchUserV2')
        raise


def transactions(log:Logger, user_id:int, limit: int|None) -> Iterator[Transaction]:
    sql="select * from transactions where user_id = @user_id order by transaction_timestamp"
    params={"user_id":user_id}
    param_types={"user_id":spanner.param_types.INT64}
    if limit is not None:
        sql += " LIMIT @limit"
        params['limit'] = limit
        param_types['limit'] = spanner.param_types.INT64
    try:
        with database.snapshot() as db:
            results=db.execute_sql(sql=sql,params=params,param_types=param_types)
            yield from _yield_response_payload(log,Transaction,results)
    except Exception as exc:
        log.error(f'Unable to retrieve data : {exc}', operation='FetchTransactions')
        raise


def transactions_v2(log:Logger, user_id:int, limit: int|None) -> Iterator[TransactionV2]:
    sql="select * from transactions where user_id = @user_id order by transaction_timestamp"
    params={"user_id":user_id}
    param_types={"user_id":spanner.param_types.INT64}
    if limit is not None:
        sql += " LIMIT @limit"
        params['limit'] = limit
        param_types['limit'] = spanner.param_types.INT64
    try:
        with database.snapshot() as db:
            results=db.execute_sql(sql=sql,params=params,param_types=param_types)
            yield from _yield_response_payload_v2(log,TransactionV2,results)
    except Exception as exc:
        log.error(f'Unable to retrieve data : {exc}', operation='FetchTransactionsV2')
        raise


    