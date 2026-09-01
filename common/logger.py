from uuid import uuid4
from dataclasses import dataclass,field

@dataclass(slots=True)
class Logger:
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    operation:str|None=field(default=None)
    log_level:int=field(default=10)
    allowed_logs:dict[str,int]=field(default_factory=lambda:{'debug':10,'info':20,'error':30})

    def info(self,*args,**kwargs):
        log_level=self.allowed_logs.get('info')
        if self.log_level>log_level:
            return
        msg = " ".join(map(str,args))
        tags = "".join(f'[{value}]' for value in kwargs.values())
        if self.operation is not None:
            print(f'[{self.trace_id}][{self.operation}]{tags} - {msg}')
        else:
            print(f'[{self.trace_id}]{tags} - {msg}')

    def debug(self,*args,**kwargs):
        log_level=self.allowed_logs.get('debug')
        if self.log_level>log_level:
            return
        msg = " ".join(map(str,args))
        tags = "".join(f'[{value}]' for value in kwargs.values())
        if self.operation is not None:
            print(f'[{self.trace_id}][{self.operation}]{tags} - {msg}')
        else:
            print(f'[{self.trace_id}]{tags} - {msg}')

    def error(self,*args,**kwargs):
        log_level=self.allowed_logs.get('error')
        if self.log_level>log_level:
            return
        msg = " ".join(map(str,args))
        tags = "".join(f'[{value}]' for value in kwargs.values())
        if self.operation is not None:
            print(f'[{self.trace_id}][{self.operation}]{tags} - {msg}')
        else:
            print(f'[{self.trace_id}]{tags} - {msg}')

    def __getattr__(self, name: str):
        def fallback(*args, **kwargs):
            allowed = list(self.allowed_logs.keys())
            if self.operation is not None:
                print(f"[{self.trace_id}][{self.operation}][Logger Error] Method or attribute '{name}' not configured. Allowed Methods: {allowed}")
            else:
                print(f"[{self.trace_id}][Logger Error] Method or attribute '{name}' not configured. Allowed Methods: {allowed}")
        return fallback