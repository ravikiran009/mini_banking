import os
from uuid import uuid4
from dataclasses import dataclass, field


# Class-level constant — shared across all Logger instances, zero per-instance allocation
_ALLOWED_LOGS = {'debug': 10, 'info': 20, 'error': 30}
_DEFAULT_LOG_LEVEL = _ALLOWED_LOGS.get(os.getenv("LOG_LEVEL", "info").lower(), 20)


@dataclass(slots=True)
class Logger:
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    operation: str | None = field(default=None)
    log_level: int = field(default=_DEFAULT_LOG_LEVEL)

    def _log(self, level_key: str, *args, **kwargs):
        log_level = _ALLOWED_LOGS.get(level_key, 0)
        if self.log_level > log_level:
            return
        msg = " ".join(map(str, args))
        tags = "".join(f'[{value}]' for value in kwargs.values())
        if self.operation is not None:
            print(f'[{self.trace_id}][{self.operation}]{tags} - {msg}')
        else:
            print(f'[{self.trace_id}]{tags} - {msg}')

    def info(self, *args, **kwargs):
        self._log('info', *args, **kwargs)

    def debug(self, *args, **kwargs):
        self._log('debug', *args, **kwargs)

    def error(self, *args, **kwargs):
        self._log('error', *args, **kwargs)

    def __getattr__(self, name: str):
        def fallback(*args, **kwargs):
            allowed = list(_ALLOWED_LOGS.keys())
            if self.operation is not None:
                print(f"[{self.trace_id}][{self.operation}][Logger Error] Method or attribute '{name}' not configured. Allowed Methods: {allowed}")
            else:
                print(f"[{self.trace_id}][Logger Error] Method or attribute '{name}' not configured. Allowed Methods: {allowed}")
        return fallback