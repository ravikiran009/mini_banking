import importlib
import traceback

from dataclasses import dataclass, field

from google.cloud.spanner_v1 import param_types

from common.logger import Logger 
from common.config import config, Config
from common.db import StoreSpannerExecutorSingleton, StagingSpannerExecutorPool
from common.responses import SuccessResponse, FailureResponse, ActionNotRequired
from common.exceptions import InvalidTransactionEvent, InvalidSQLTransaction


@dataclass(slots=True)
class Credit:
    logger: Logger
    event: dict
    config: Config = field(default_factory=lambda: config)
    db_executor: StoreSpannerExecutorSingleton = field(init=False)
    staging_db_executor: StagingSpannerExecutorPool = field(init=False)

    def __post_init__(self):
        self.db_executor = StoreSpannerExecutorSingleton(self.logger)
        self.staging_db_executor = StagingSpannerExecutorPool(self.logger)

    def _validate(self, user_id: int, amount: str):
        _user_details = next(self.db_executor.user(user_id), None)

        if not _user_details:
            return FailureResponse(msg=f"User {user_id} Not Found")   

        if amount<=0:
            if amount==0:
                return ActionNotRequired(msg="Credit Amount is zero no need to process the message")
            raise InvalidTransactionEvent(msg="Credit Amount cannot be less than zero")

        return SuccessResponse(msg="Event is successfully validated", resp=_user_details)

    def handle(self, user: User, credit_amount: float, trace_id:str, transaction_id: str):
        sql="""
        UPDATE users SET balance=@balance, last_transaction_id=@last_transaction_id where user_id=@user_id
        """
        store_db_params={
        "balance": float(user.balance+credit_amount),
        "last_transaction_id": transaction_id,
        "user_id": user.user_id
        }
        store_db_param_types={
            "balance": param_types.FLOAT64,
            "last_transaction_id": param_types.STRING,
            "user_id": param_types.INT64
        }
        staging_sql="""
        UPDATE transactions_staging SET status=@status where trace_id=@trace_id
        """
        staging_params={
            "status": 3,
            "trace_id": trace_id
        }
        staging_param_types={
            "status": param_types.INT64,
            "trace_id": param_types.STRING
        }
        try:
            resp=self.db_executor.update(sql=sql, params=store_db_params, param_types=store_db_param_types)
            if isinstance(resp, SuccessResponse):
                staging_resp=self.staging_db_executor.update(sql=staging_sql, params=staging_params, param_types=staging_param_types)
                if isinstance(staging_resp, SuccessResponse):
                    return SuccessResponse(msg=f"Successfully processed transaction. Trace_Id: {trace_id}, Transaction_Id: {transaction_id}.")
                return FailureResponse(msg=f"Failed processing transaction at staging db level. Staging executor resp: {staging_resp.msg}. Trace_Id: {trace_id}, Transaction_Id: {transaction_id}.")
            # Mark event failed, revert store db state
            store_db_params["balance"]=user.balance
            store_db_params["last_transaction_id"]=user.last_transaction_id
            staging_params["status"]=4
            resp=self.db_executor.update(sql=sql, params=store_db_params, param_types=store_db_param_types)
            staging_resp=self.staging_db_executor.update(sql=staging_sql, params=staging_params, param_types=staging_param_types)
            return FailureResponse(msg=f"Failed processing transaction at store db level. Store executor resp: {resp.msg}. Trace_Id: {trace_id}, Transaction_Id: {transaction_id}.")
        except InvalidSQLTransaction as exc:
            return FailureResponse(msg=exc.msg+"$$$"+traceback.format_exc().replace("\n","$$$"))
        except Exception as exc:
            self.logger.error("Error in CreditEventHander: ", exc, operation="CreditEventHandler")
            return FailureResponse(msg=str(exc)+"$$$"+traceback.format_exc().replace("\n","$$$"))

    def process(self):
        user_id=self.event.get("user_id")
        credit_amount=self.event.get("amount")
        trace_id=self.event.get("trace_id")
        transaction_id=self.event.get('transaction_id')
        self.logger.info(f"Credit event {transaction_id} processing...")
        try:
            resp_object = self._validate(user_id=user_id, amount=credit_amount)
            if isinstance(resp_object, FailureResponse):
                return resp_object
        except InvalidSQLTransaction as exc:
            return FailureResponse(msg=exc.msg)
        except InvalidTransactionEvent as exc:
            self.logger.error("Unable to validate event because of invalid request submission: ", exc.msg)
            return FailureResponse(msg=str(exc)+"$$$"+traceback.format_exc().replace("\n","$$$"), status_code=422)
        except Exception as exc:
            self.logger.error("Unable to validate event: ", exc)
            return FailureResponse(msg=str(exc)+"$$$"+traceback.format_exc().replace("\n","$$$"), status_code=422)
        self.logger.info(f"Credit event {transaction_id} validated successfully")
        if isinstance(resp_object, ActionNotRequired):
            self.logger.info(f"Credit event {transaction_id} no need to process")
            return SuccessResponse(
                msg="Event is successfully processed", 
                resp={
                    "status":"successful", 
                    "trace_id": trace_id,
                    "transaction_id":transaction_id
                }
            )
        self.logger.info(f"Credit event {transaction_id} handler started...")
        handler_resp=self.handle(user=resp_object.resp, credit_amount=credit_amount, trace_id=trace_id, transaction_id=transaction_id)
        if isinstance(handler_resp, SuccessResponse):
            handler_resp.resp={
                "status":"successful", 
                "trace_id": trace_id,
                "transaction_id":transaction_id
            }
        return handler_resp
            
    
@dataclass(slots=True)
class Debit:
    logger: Logger
    event: dict
    config: Config = field(default_factory=lambda: config)
    db_executor: StoreSpannerExecutorSingleton = field(init=False)
    staging_db_executor: StagingSpannerExecutorPool = field(init=False)

    def __post_init__(self):
        self.db_executor = StoreSpannerExecutorSingleton(self.logger)
        self.staging_db_executor = StagingSpannerExecutorPool(self.logger)

    def _validate(self, user_id: int, amount: str):
        _user_details = next(self.db_executor.user(user_id), None)

        if not _user_details:
            return FailureResponse(msg=f"User {user_id} Not Found")   

        if amount<=0:
            if amount==0:
                return ActionNotRequired(msg="Debit Amount is zero no need to process the message")
            raise InvalidTransactionEvent(msg="Debit Amount cannot be less than zero")

        if amount>_user_details.balance:
            raise InvalidTransactionEvent(msg="Debit Amount cannot be greater than balance")

        return SuccessResponse(msg="Event is successfully validated", resp=_user_details)

    def handle(self, user: User, debit_amount: float, trace_id:str, transaction_id: str):
        sql="""
        UPDATE users SET balance=@balance, last_transaction_id=@last_transaction_id where user_id=@user_id
        """
        store_db_params={
        "balance": float(user.balance-debit_amount),
        "last_transaction_id": transaction_id,
        "user_id": user.user_id
        }
        store_db_param_types={
            "balance": param_types.FLOAT64,
            "last_transaction_id": param_types.STRING,
            "user_id": param_types.INT64
        }
        staging_sql="""
        UPDATE transactions_staging SET status=@status where trace_id=@trace_id
        """
        staging_params={
            "status": 3,
            "trace_id": trace_id
        }
        staging_param_types={
            "status": param_types.INT64,
            "trace_id": param_types.STRING
        }
        try:
            resp=self.db_executor.update(sql=sql, params=store_db_params, param_types=store_db_param_types)
            if isinstance(resp, SuccessResponse):
                staging_resp=self.staging_db_executor.update(sql=staging_sql, params=staging_params, param_types=staging_param_types)
                if isinstance(staging_resp, SuccessResponse):
                    return SuccessResponse(msg=f"Successfully processed transaction. Trace_Id: {trace_id}, Transaction_Id: {transaction_id}.")
                return FailureResponse(msg=f"Failed processing transaction at staging db level. Staging executor resp: {staging_resp.msg}. Trace_Id: {trace_id}, Transaction_Id: {transaction_id}.")
            # Mark event failed, revert store db state
            store_db_params["balance"]=user.balance
            store_db_params["last_transaction_id"]=user.last_transaction_id
            staging_params["status"]=4
            resp=self.db_executor.update(sql=sql, params=store_db_params, param_types=store_db_param_types)
            staging_resp=self.staging_db_executor.update(sql=staging_sql, params=staging_params, param_types=staging_param_types)
            return FailureResponse(msg=f"Failed processing transaction at store db level. Store executor resp: {resp.msg}. Trace_Id: {trace_id}, Transaction_Id: {transaction_id}.")
        except InvalidSQLTransaction as exc:
            return FailureResponse(msg=exc.msg+"$$$"+traceback.format_exc().replace("\n","$$$"))
        except Exception as exc:
            self.logger.error("Error in DebitEventHander: ", exc, operation="DebitEventHandler")
            return FailureResponse(msg=str(exc)+"$$$"+traceback.format_exc().replace("\n","$$$"))

    def process(self):
        user_id=self.event.get("user_id")
        debit_amount=self.event.get("amount")
        trace_id=self.event.get("trace_id")
        transaction_id=self.event.get('transaction_id')
        self.logger.info(f"Debit event {transaction_id} processing...")
        try:
            resp_object = self._validate(user_id=user_id, amount=debit_amount)
            if isinstance(resp_object, FailureResponse):
                return resp_object
        except InvalidSQLTransaction as exc:
            return FailureResponse(msg=exc.msg)
        except InvalidTransactionEvent as exc:
            self.logger.error("Unable to validate event because of invalid request submission: ", exc.msg)
            return FailureResponse(msg=str(exc)+"$$$"+traceback.format_exc().replace("\n","$$$"), status_code=422)
        except Exception as exc:
            self.logger.error("Unable to validate event: ", exc)
            return FailureResponse(msg=str(exc)+"$$$"+traceback.format_exc().replace("\n","$$$"), status_code=422)
        self.logger.info(f"Debit event {transaction_id} validated successfully")
        if isinstance(resp_object, ActionNotRequired):
            self.logger.info(f"Credit event {transaction_id} no need to process")
            return SuccessResponse(
                msg="Event is successfully processed", 
                resp={
                    "status":"successful", 
                    "trace_id": trace_id,
                    "transaction_id":transaction_id
                }
            )
        self.logger.info(f"Debit event {transaction_id} handler started...")
        handler_resp=self.handle(user=resp_object.resp, debit_amount=debit_amount, trace_id=trace_id, transaction_id=transaction_id)
        if isinstance(handler_resp, SuccessResponse):
            handler_resp.resp={
                "status":"successful", 
                "trace_id": trace_id,
                "transaction_id":transaction_id
            }
        return handler_resp

    
@dataclass(slots=True)
class Transfer:
    logger: Logger

    def process(self, event):
        self.logger.info(f"Transfer event {event.get('transaction_id')}")


HANDLERS = {
    "Credit" : Credit,
    "Debit" : Debit,
    "Transfer" : Transfer
}


@dataclass(slots=True)
class TransactionProcessor:
    logger: Logger
    event: dict

    def process(self):
        try:
            # event_handler = globals()[self.transaction_type](self.logger)
            # module = importlib.import_module(name="processor.event_handler.handler")
            # cls = getattr(module,self.transaction_type)
            # event_handler = cls(self.logger)
            txn_type = self.event.get("transaction_type").title()
            event_handler_cls = HANDLERS.get(txn_type)
            if not self.event.get("user_id") or not self.event.get("trace_id") or not self.event.get("transaction_id") or not self.event.get("amount"):
                msg="Invalid transaction - event details found"
                raise InvalidTransactionEvent(msg=msg)
            if not event_handler_cls:
                msg=f"{txn_type} is not allowed, Allowed types: {tuple(HANDLERS.keys())}"
                raise InvalidTransactionEvent(msg=msg)
            event_handler = event_handler_cls(self.logger, self.event)
            handler_resp=event_handler.process()
            return handler_resp
        except InvalidTransactionEvent as exc:
            return FailureResponse(msg="TransactionProcessor failed"+"$$$"+str(exc.msg)+"$$$"+traceback.format_exc().replace("\n","$$$"))
        except Exception as exc:
            return FailureResponse(msg="TransactionProcessor failed"+"$$$"+str(exc)+"$$$"+traceback.format_exc().replace("\n","$$$"))