from uuid import uuid4
from dataclasses import asdict
from fastapi import FastAPI
from common.logger import Logger

from processor.tests.time_memory_tests import User, UserNoSlots, UserSlots, UserV2, UserV2NoSlots, UserV2Slots

app = FastAPI()

@app.get("/")
def health():
    return "Health Check Successful ✅"


@app.get("/users")
def get_users(data:list[User]|list[UserNoSlots]|list[UserSlots]):
    log = Logger(trace_id=str(uuid4()))
    try:
        if not data:
            return []
        return [item.model_dump(by_alias=True, exclude_none=True) for item in data]
    except:
        return "An unexpected error occured. Please try again later"

@app.get("/users_pass_pydantic")
def get_users_pass_pydantic(data:list[User]|list[UserNoSlots]|list[UserSlots]):
    log = Logger(trace_id=str(uuid4()))
    try:
        if not data:
            return []
        return data
    except:
        return "An unexpected error occured. Please try again later"


@app.get("/v2/users")
def get_users_v2(data:list[UserV2]|list[UserV2NoSlots]|list[UserV2Slots]):
    log = Logger(trace_id=str(uuid4()))
    try:
        if not data:
            return []
        return [asdict(item) for item in data]
    except:
        return "An unexpected error occured. Please try again later"

@app.get("/v2/users_pass_dataclass")
def get_users_v2_pass_dataclass(data:list[UserV2]|list[UserV2NoSlots]|list[UserV2Slots]):
    log = Logger(trace_id=str(uuid4()))
    try:
        if not data:
            return []
        return data
    except:
        return "An unexpected error occured. Please try again later"

if __name__=='__main__':
    #================= Commence Memory and Time Performace Tests through FastAPI =================#
    from common.logger import Logger
    import tracemalloc
    import random
    import time

    log=Logger(trace_id='FastAPIPerformanceTest')

    data_size = 10_000_000
    print(data_size)

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
    res = get_users(data)
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
    res = get_users(data)
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
    res = get_users(data)
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
    res = get_users_v2(data)
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
    res = get_users_v2(data)
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
    res = get_users_v2(data)
    cur, peak = tracemalloc.get_traced_memory()
    en = time.perf_counter()
    log.info(f'Time consumed: {(en-st)*1000} milliseconds', object='ListOfDataClassUserNoSlots')
    log.info(f'Memory consumed: {cur} bytes, {peak} bytes', object='ListOfDataClassUserNoSlots')
    tracemalloc.stop()

# Test data size: 10
# [FastAPIPerformanceTest][ListOfPydanticUser] - Time consumed: 0.23230002261698246 milliseconds
# [FastAPIPerformanceTest][ListOfPydanticUser] - Memory consumed: 6792 bytes, 7061 bytes
# [FastAPIPerformanceTest][ListOfPydanticUserSlots] - Time consumed: 0.13619998935610056 milliseconds
# [FastAPIPerformanceTest][ListOfPydanticUserSlots] - Memory consumed: 7144 bytes, 7511 bytes
# [FastAPIPerformanceTest][ListOfPydanticUserNoSlots] - Time consumed: 0.13329999637790024 milliseconds
# [FastAPIPerformanceTest][ListOfPydanticUserNoSlots] - Memory consumed: 6024 bytes, 6391 bytes
# [FastAPIPerformanceTest][ListOfDataClassUser] - Time consumed: 0.13050000416114926 milliseconds
# [FastAPIPerformanceTest][ListOfDataClassUser] - Memory consumed: 3624 bytes, 4277 bytes
# [FastAPIPerformanceTest][ListOfDataClassUserSlots] - Time consumed: 0.15040001017041504 milliseconds
# [FastAPIPerformanceTest][ListOfDataClassUserSlots] - Memory consumed: 1408 bytes, 2061 bytes       
# [FastAPIPerformanceTest][ListOfDataClassUserNoSlots] - Time consumed: 0.15509998775087297 milliseconds
# [FastAPIPerformanceTest][ListOfDataClassUserNoSlots] - Memory consumed: 3624 bytes, 4277 bytes

# Test data size: 10000000
# [FastAPIPerformanceTest][ListOfPydanticUser]          - Time consumed: 101049.96889998438 milliseconds
# [FastAPIPerformanceTest][ListOfPydanticUser]          - Memory consumed: 8137068021 bytes, 8137068290 bytes
# [FastAPIPerformanceTest][ListOfPydanticUserSlots]     - Time consumed: 154125.08319999324 milliseconds
# [FastAPIPerformanceTest][ListOfPydanticUserSlots]     - Memory consumed: 8137060661 bytes, 8137060930 bytes
# [FastAPIPerformanceTest][ListOfPydanticUserNoSlots]   - Time consumed: 173672.85059997812 milliseconds
# [FastAPIPerformanceTest][ListOfPydanticUserNoSlots]   - Memory consumed: 8137042925 bytes, 8137043194 bytes
# [FastAPIPerformanceTest][ListOfDataClassUser]         - Time consumed: 159068.0655000033 milliseconds
# [FastAPIPerformanceTest][ListOfDataClassUser]         - Memory consumed: 4217056453 bytes, 4217056922 bytes
# [FastAPIPerformanceTest][ListOfDataClassUserSlots]    - Time consumed: 164909.84300000127 milliseconds
# [FastAPIPerformanceTest][ListOfDataClassUserSlots]    - Memory consumed: 3817068053 bytes, 3817068522 bytes
# [FastAPIPerformanceTest][ListOfDataClassUserNoSlots]  - Time consumed: 184491.852200008 milliseconds
# [FastAPIPerformanceTest][ListOfDataClassUserNoSlots]  - Memory consumed: 4217070989 bytes, 4217071458 bytes