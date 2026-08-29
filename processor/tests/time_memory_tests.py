from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

from dataclasses import dataclass


class User(BaseModel) : 
    model_config = ConfigDict(populate_by_name = True, extra = 'forbid')

    user_id : int = Field(alias = 'UserId')
    account_id : str = Field(alias = 'AccountId')
    balance : int = Field(alias = 'Balance')
    last_transaction_id : str | None = Field(default=None, alias = 'LastTransactionId')
class UserSlots(BaseModel) : 
    model_config = ConfigDict(populate_by_name = True, extra = 'forbid', slots=True)

    user_id : int = Field(alias = 'UserId')
    account_id : str = Field(alias = 'AccountId')
    balance : int = Field(alias = 'Balance')
    last_transaction_id : str | None = Field(alias = 'LastTransactionId')
class UserNoSlots(BaseModel) : 
    model_config = ConfigDict(populate_by_name = True, extra = 'forbid', slots=False)

    user_id : int = Field(alias = 'UserId')
    account_id : str = Field(alias = 'AccountId')
    balance : int = Field(alias = 'Balance')
    last_transaction_id : str | None = Field(alias = 'LastTransactionId')


@dataclass
class UserV2:
    user_id : int
    account_id : str
    balance : int
    last_transaction_id : str | None = None
@dataclass(slots=True)
class UserV2Slots:
    user_id : int
    account_id : str
    balance : int
    last_transaction_id : str | None = None
@dataclass(slots=False)
class UserV2NoSlots:
    user_id : int
    account_id : str
    balance : int
    last_transaction_id : str | None = None

if __name__=='__main__':
    #================= Commence Memory and Time Performace Tests =================#
    from common.logger import Logger
    import tracemalloc
    import random
    import time

    log=Logger(trace_id='PerformanceTest')

    data_size = 10_000_000

    tracemalloc.start()
    st = time.perf_counter()
    data = [
        dict(
            user_id = i,
            account_id = f'acc_{i:03d}',
            balance = random.randint(50_000, 5_00_000),
            last_transaction_id = None
        )
        for i in range(1,data_size+1)
    ]
    cur, peak = tracemalloc.get_traced_memory()
    en = time.perf_counter()
    log.info(f'Time consumed: {(en-st)*1000} milliseconds', object='ListOfDict')
    log.info(f'Memory consumed: {cur} bytes, {peak} bytes', object='ListOfDict')
    tracemalloc.stop()

    tracemalloc.start()
    st = time.perf_counter()
    data = [
        User(
            user_id = i,
            account_id = f'acc_{i:03d}',
            balance = random.randint(50_000, 5_00_000),
            last_transaction_id = None
        )
        for i in range(1,data_size+1)
    ]
    cur, peak = tracemalloc.get_traced_memory()
    en = time.perf_counter()
    log.info(f'Time consumed: {(en-st)*1000} milliseconds', object='ListOfPydanticUser')
    log.info(f'Memory consumed: {cur} bytes, {peak} bytes', object='ListOfPydanticUser')
    tracemalloc.stop()

    tracemalloc.start()
    st = time.perf_counter()
    data = [
        UserSlots(
            user_id = i,
            account_id = f'acc_{i:03d}',
            balance = random.randint(50_000, 5_00_000),
            last_transaction_id = None
        )
        for i in range(1,data_size+1)
    ]
    cur, peak = tracemalloc.get_traced_memory()
    en = time.perf_counter()
    log.info(f'Time consumed: {(en-st)*1000} milliseconds', object='ListOfPydanticUserSlots')
    log.info(f'Memory consumed: {cur} bytes, {peak} bytes', object='ListOfPydanticUserSlots')
    tracemalloc.stop()

    tracemalloc.start()
    st = time.perf_counter()
    data = [
        UserNoSlots(
            user_id = i,
            account_id = f'acc_{i:03d}',
            balance = random.randint(50_000, 5_00_000),
            last_transaction_id = None
        )
        for i in range(1,data_size+1)
    ]
    cur, peak = tracemalloc.get_traced_memory()
    en = time.perf_counter()
    log.info(f'Time consumed: {(en-st)*1000} milliseconds', object='ListOfPydanticUserNoSlots')
    log.info(f'Memory consumed: {cur} bytes, {peak} bytes', object='ListOfPydanticUserNoSlots')
    tracemalloc.stop()

    tracemalloc.start()
    st = time.perf_counter()
    data = [
        UserV2(
            user_id = i,
            account_id = f'acc_{i:03d}',
            balance = random.randint(50_000, 5_00_000),
            last_transaction_id = None
        )
        for i in range(1,data_size+1)
    ]
    cur, peak = tracemalloc.get_traced_memory()
    en = time.perf_counter()
    log.info(f'Time consumed: {(en-st)*1000} milliseconds', object='ListOfDataClassUser')
    log.info(f'Memory consumed: {cur} bytes, {peak} bytes', object='ListOfDataClassUser')
    tracemalloc.stop()

    tracemalloc.start()
    st = time.perf_counter()
    data = [
        UserV2Slots(
            user_id = i,
            account_id = f'acc_{i:03d}',
            balance = random.randint(50_000, 5_00_000),
            last_transaction_id = None
        )
        for i in range(1,data_size+1)
    ]
    cur, peak = tracemalloc.get_traced_memory()
    en = time.perf_counter()
    log.info(f'Time consumed: {(en-st)*1000} milliseconds', object='ListOfDataClassUserSlots')
    log.info(f'Memory consumed: {cur} bytes, {peak} bytes', object='ListOfDataClassUserSlots')
    tracemalloc.stop()

    tracemalloc.start()
    st = time.perf_counter()
    data = [
        UserV2NoSlots(
            user_id = i,
            account_id = f'acc_{i:03d}',
            balance = random.randint(50_000, 5_00_000),
            last_transaction_id = None
        )
        for i in range(1,data_size+1)
    ]
    cur, peak = tracemalloc.get_traced_memory()
    en = time.perf_counter()
    log.info(f'Time consumed: {(en-st)*1000} milliseconds', object='ListOfDataClassUserNoSlots')
    log.info(f'Memory consumed: {cur} bytes, {peak} bytes', object='ListOfDataClassUserNoSlots')
    tracemalloc.stop()


# Test results for data_size: 10
# [PerformanceTest][ListOfDict]                   - Time consumed: 0.06399999256245792 milliseconds
# [PerformanceTest][ListOfDict]                   - Memory consumed: 1384 bytes, 1384 bytes
# [PerformanceTest][ListOfPydanticUser]           - Time consumed: 0.11239998275414109 milliseconds
# [PerformanceTest][ListOfPydanticUser]           - Memory consumed: 7848 bytes, 7896 bytes
# [PerformanceTest][ListOfPydanticUserSlots]      - Time consumed: 0.07509998977184296 milliseconds
# [PerformanceTest][ListOfPydanticUserSlots]      - Memory consumed: 5896 bytes, 5944 bytes
# [PerformanceTest][ListOfPydanticUserNoSlots]    - Time consumed: 0.0850000069476664 milliseconds
# [PerformanceTest][ListOfPydanticUserNoSlots]    - Memory consumed: 5896 bytes, 5944 bytes
# [PerformanceTest][ListOfDataClassUser]          - Time consumed: 0.08699999307282269 milliseconds
# [PerformanceTest][ListOfDataClassUser]          - Memory consumed: 3496 bytes, 3544 bytes
# [PerformanceTest][ListOfDataClassUserSlots]     - Time consumed: 0.09879999561235309 milliseconds
# [PerformanceTest][ListOfDataClassUserSlots]     - Memory consumed: 1280 bytes, 1328 bytes
# [PerformanceTest][ListOfDataClassUserNoSlots]   - Time consumed: 0.16700002015568316 milliseconds
# [PerformanceTest][ListOfDataClassUserNoSlots]   - Memory consumed: 3496 bytes, 3544 bytes

# Test results for data_size: 10_000_000
# [PerformanceTest][ListOfDict]                   - Time consumed: 41319.13889999851 milliseconds
# [PerformanceTest][ListOfDict]                   - Memory consumed: 3087973813 bytes, 3087973813 bytes
# [PerformanceTest][ListOfPydanticUser]           - Time consumed: 90843.73449999839 milliseconds
# [PerformanceTest][ListOfPydanticUser]           - Memory consumed: 6207980205 bytes, 6207980253 bytes
# [PerformanceTest][ListOfPydanticUserSlots]      - Time consumed: 99511.88319997163 milliseconds
# [PerformanceTest][ListOfPydanticUserSlots]      - Memory consumed: 6207962421 bytes, 6207962469 bytes
# [PerformanceTest][ListOfPydanticUserNoSlots]    - Time consumed: 125231.97550000623 milliseconds
# [PerformanceTest][ListOfPydanticUserNoSlots]    - Memory consumed: 6207962421 bytes, 6207962469 bytes
# [PerformanceTest][ListOfDataClassUser]          - Time consumed: 97318.45669998438 milliseconds
# [PerformanceTest][ListOfDataClassUser]          - Memory consumed: 2287975733 bytes, 2287975781 bytes
# [PerformanceTest][ListOfDataClassUserSlots]     - Time consumed: 111356.39020000235 milliseconds
# [PerformanceTest][ListOfDataClassUserSlots]     - Memory consumed: 1887972821 bytes, 1887972869 bytes
# [PerformanceTest][ListOfDataClassUserNoSlots]   - Time consumed: 128628.48780001514 milliseconds
# [PerformanceTest][ListOfDataClassUserNoSlots]   - Memory consumed: 2287975789 bytes, 2287975837 bytes