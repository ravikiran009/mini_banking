import os
import time

from functools import wraps
from contextlib import contextmanager

# Decorator function to track performance of functions with condensed per-transaction metrics
def performancetracker(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        st = time.perf_counter()
        res = func(*args, **kwargs)
        en = time.perf_counter()
        data = kwargs.get("data") if "data" in kwargs else (args[0] if args and isinstance(args[0], dict) else None)
        extra = ""
        if isinstance(data, dict):
            tx_type = data.get("transaction_type")
            tx_id = data.get("transaction_id")
            if tx_type and tx_id:
                extra = f" [{tx_type} {tx_id}]"
            elif tx_type:
                extra = f" [{tx_type}]"
            elif tx_id:
                extra = f" [{tx_id}]"
        print(f"[PerformanceTracker] Time consumed for {func.__name__}{extra}: {en-st:.6f} seconds")
        return res
    return wrapper

import atexit
import threading
import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Singleton session instance and lock to guarantee only one session is created
_session: Session | None = None
_session_lock = threading.Lock()

def get_session() -> Session:
    """Returns the singleton Session, initializing it once in a thread-safe manner with auto-retries."""
    global _session
    if _session is None:
        with _session_lock:
            if _session is None:
                s = Session()
                # Automatically retry dropped/reset connections and transient HTTP errors
                retries = Retry(
                    total=3,
                    backoff_factor=0.2,
                    status_forcelist=[500, 502, 503, 504],
                    raise_on_status=False
                )
                adapter = HTTPAdapter(max_retries=retries, pool_connections=20, pool_maxsize=20)
                s.mount("http://", adapter)
                s.mount("https://", adapter)
                _session = s
    return _session

def close_session():
    """Explicitly closes and resets the singleton Session."""
    global _session
    with _session_lock:
        if _session is not None:
            try:
                _session.close()
            except Exception:
                pass
            _session = None

# Automatically cleanup the session when Python process exits
atexit.register(close_session)

# Context manager for request Session with self-healing on corruption
@contextmanager
def safe_connect_session():
    """Yields the shared singleton Session, ensuring only one session is created.
    If a network corruption/interruption occurs, automatically resets the session.
    """
    session = get_session()
    try:
        yield session
    except (requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.Timeout):
        close_session()
        raise