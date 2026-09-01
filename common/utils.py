import time
from functools import wraps

# Decorator function to track performance of functions
def performancetracker(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        st=time.perf_counter()
        res=func(*args,**kwargs)
        en=time.perf_counter()
        print(f"[PerformanceTracker] Time consumed for {func.__name__}: {en-st:.6f} seconds")
        return res
    return wrapper