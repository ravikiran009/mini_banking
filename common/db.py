import os
import pandas as pd

from uuid import uuid4
from typing import TypeVar
from pydantic import BaseModel,ValidationError
from collections.abc import Iterator

from google.cloud import spanner
from google.cloud.spanner_v1.streamed import StreamedResultSet
from google.cloud.spanner_v1.pool import BurstyPool

from common.logger import Logger
from common.models.user import User, UserV2
from common.models.transaction import Transaction, TransactionV2
from common.exceptions import InvalidSQLTransaction
from common.responses import SuccessResponse, FailureResponse


# Read GCP / Spanner configurations from environment variables
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
STORE_INSTANCE_ID = os.getenv("SPANNER_STORE_INSTANCE_ID")
STORE_DATABASE_ID = os.getenv("SPANNER_STORE_DATABASE_ID")

STAGING_INSTANCE_ID = os.getenv("SPANNER_STAGING_INSTANCE_ID")
STAGING_DATABASE_ID = os.getenv("SPANNER_STAGING_DATABASE_ID")

# Initialize Once when module loads
client = spanner.Client(project=GCP_PROJECT_ID)
database_instance = client.instance(instance_id=STORE_INSTANCE_ID)
_database = database_instance.database(database_id=STORE_DATABASE_ID)

# Create a pool of SpannerStagingInstances
_pool = BurstyPool(target_size=10)
staging_database_instance = client.instance(instance_id=STAGING_INSTANCE_ID)
_staging_database = staging_database_instance.database(database_id=STAGING_DATABASE_ID, pool=_pool)


class StoreSpannerExecutorSingleton:
    def __init__(self,logger:Logger):
        self.logger = logger
        self.database = _database

    def _yield_response_payload(self,model_class:type[BaseModel],data:StreamedResultSet) -> Iterator[BaseModel]:
        # keys = model_class.model_fields.keys()
        # self.logger.debug(keys,check="Attrs")
        col_names = None
        for row in data:
            if not col_names:
                col_names = [field.name for field in data.fields]
            row_dict = dict(zip(col_names, row))
            # self.logger.debug(row_dict,check="Values")
            item = model_class.model_validate(row_dict)
            yield item

    T = TypeVar("T")

    def _yield_response_payload_v2(self,model_class:type[T],data:StreamedResultSet) -> Iterator[T]:
        # keys = model_class.__slots__
        # self.logger.debug(keys,check="AttrsV2")
        col_names = None
        for row in data:
            if not col_names:
                col_names = [field.name for field in data.fields]
            row_dict = dict(zip(col_names, row))
            # self.logger.debug(row_dict,check="ValuesV2")
            item = model_class(**row_dict)
            yield item        

    def user(self, user_id:int) -> Iterator[User]:
        sql="select * from users where user_id = @user_id"
        params={"user_id":user_id}
        param_types={"user_id":spanner.param_types.INT64}
        try:
            with self.database.snapshot() as db:
                results=db.execute_sql(sql=sql,params=params,param_types=param_types)
                yield from self._yield_response_payload(User,results)
        except Exception as exc:
            self.logger.error(f"Unable to retrieve data : {exc}", operation="FetchUser")
            raise InvalidSQLTransaction(msg=str(exc))

    def user_v2(self, user_id:int) -> Iterator[UserV2]:
        sql="select * from users where user_id = @user_id"
        params={"user_id":user_id}
        param_types={"user_id":spanner.param_types.INT64}
        try:
            with self.database.snapshot() as db:
                results=db.execute_sql(sql=sql,params=params,param_types=param_types)
                yield from self._yield_response_payload_v2(UserV2,results)
        except Exception as exc:
            self.logger.error(f"Unable to retrieve data : {exc}", operation="FetchUserV2")
            raise InvalidSQLTransaction(msg=str(exc))

    def transactions(self, user_id:int, limit: int|None) -> Iterator[Transaction]:
        sql="select * from transactions where user_id = @user_id order by transaction_timestamp"
        params={"user_id":user_id}
        param_types={"user_id":spanner.param_types.INT64}
        if limit is not None:
            sql += " LIMIT @limit"
            params["limit"] = limit
            param_types["limit"] = spanner.param_types.INT64
        try:
            with self.database.snapshot() as db:
                results=db.execute_sql(sql=sql,params=params,param_types=param_types)
                yield from self._yield_response_payload(Transaction,results)
        except Exception as exc:
            self.logger.error(f"Unable to retrieve data : {exc}", operation="FetchTransactions")
            raise InvalidSQLTransaction(msg=str(exc))

    def transactions_v2(self, user_id:int, limit: int|None) -> Iterator[TransactionV2]:
        sql="select * from transactions where user_id = @user_id order by transaction_timestamp"
        params={"user_id":user_id}
        param_types={"user_id":spanner.param_types.INT64}
        if limit is not None:
            sql += " LIMIT @limit"
            params["limit"] = limit
            param_types["limit"] = spanner.param_types.INT64
        try:
            with self.database.snapshot() as db:
                results=db.execute_sql(sql=sql,params=params,param_types=param_types)
                yield from self._yield_response_payload_v2(TransactionV2,results)
        except Exception as exc:
            self.logger.error(f"Unable to retrieve data : {exc}", operation="FetchTransactionsV2")
            raise InvalidSQLTransaction(msg=str(exc))

    def update(self, sql: str, params: dict|None = None, param_types: dict|None = None):
        if not sql:
            self.logger.info("Nothing to run", operation="ExecuteSQL")
            return
        if params:
            if not param_types:
                self.logger.error("Param Types have to be defined if params is passed", operation="ExecuteSQL:StoreDb")
                raise InvalidSQLTransaction(msg="Param Types not passed")
            if not set(params).issubset(set(param_types)):
                self.logger.error("Param Types missing: ",set(params)-set(param_types), operation="ExecuteSQL:StoreDb")
                raise InvalidSQLTransaction(msg="Param Types missing")
        try:
            self.database.run_in_transaction(lambda txn: txn.execute_update(dml=sql, params=params, param_types=param_types))
            self.logger.info(f"Executing sql: {sql}, params: {params}, param_types: {param_types}", operation="ExecuteSQL:StoreDb")
            return SuccessResponse(msg="Sql executed successfully")
        except Exception as exc:
            self.logger.error("Unable to process sql transaction",exc,operation="ExecuteSQL:StoreDb")
            return FailureResponse(msg="Unable to process sql transaction "+str(exc))


class StagingSpannerExecutorPool:
    _staging_instances = None

    def __init__(self,logger:Logger):
        self.logger = logger
        self.database = _staging_database

    def _yield_events(self, data: StreamedResultSet, batch_size: int = 2):
        # data = data.to_dict_list()
        columns = None
        cur_size = 0
        events = list()
        failed_transaction_users_set = set()
        for row in data:
            if not columns:
                columns = [field.name for field in data.fields]
                user_id_idx   = columns.index("user_id")
                status_idx    = columns.index("status")
                from_user_idx = columns.index("from_user")
            user_id = row[user_id_idx]
            status  = row[status_idx]
            from_user  = row[from_user_idx]
            if status==4:
                failed_transaction_users_set.add(user_id)
                if not from_user:
                    failed_transaction_users_set.add(from_user)

            if user_id in failed_transaction_users_set or from_user in failed_transaction_users_set:
                continue

            events.append(row)
            cur_size += 1
            
            if cur_size >= batch_size:
                df = pd.DataFrame(data=events, columns=columns)
                if "from_user" in df.columns:
                    df["from_user"] = df["from_user"].astype("Int64")
                if "user_id" in df.columns:
                    df["user_id"] = df["user_id"].astype("Int64")
                yield df
                cur_size = 0
                events = list()
        
        if events:
            df = pd.DataFrame(data=events, columns=columns)
            if "from_user" in df.columns:
                df["from_user"] = df["from_user"].astype("Int64")
            if "user_id" in df.columns:
                df["user_id"] = df["user_id"].astype("Int64")
            yield df
        
    def get_transaction_events(self):
        # Status=3 -> Successful, Status=1 -> Yet to Process, Status=4 -> Failed
        sql="select * from transactions_staging where status<>3 order by received_timestamp, user_id"
        try:
            with self.database.snapshot() as db:
                results=db.execute_sql(sql=sql)
                yield from self._yield_events(results)
        except Exception as exc:
            # import traceback
            # traceback.print_exception(exc)
            self.logger.error(f"Unable to retrieve data from staging db: {exc}", operation="FetchStagedTransactions")
    
    def update(self, sql: str, params: dict|None = None, param_types: dict|None = None):
        if not sql:
            self.logger.info("Nothing to run", operation="ExecuteSQL")
            return
        if params:
            if not param_types:
                self.logger.error("Param Types have to be defined if params is passed", operation="ExecuteSQL:StagingDb")
                raise InvalidSQLTransaction(msg="Param Types not passed")
            if not set(params).issubset(set(param_types)):
                self.logger.error("Param Types missing: ",set(params)-set(param_types), operation="ExecuteSQL:StagingDb")
                raise InvalidSQLTransaction(msg="Param Types missing")
        try:
            self.database.run_in_transaction(lambda txn: txn.execute_update(dml=sql, params=params, param_types=param_types))
            self.logger.info(f"Executing sql: {sql}, params: {params}, param_types: {param_types}", operation="ExecuteSQL:StagingDb")
            return SuccessResponse(msg="Sql executed successfully")
        except Exception as exc:
            self.logger.error("Unable to proxess sql transaction",exc,operation="ExecuteSQL:StagingDb")
            return FailureResponse(msg="Unable to process sql transaction"+str(exc))