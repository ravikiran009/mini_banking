from dataclasses import dataclass,field

@dataclass(slots=True)
class Logger:
    trace_id:str
    log_level:int=field(default=10)
    allowed_logs:dict[str,int]=field(default_factory=lambda:{'debug':10,'info':20,'error':30})

    def info(self,*args,**kwargs):
        log_level=self.allowed_logs.get('info')
        if self.log_level>log_level:
            return
        msg = " ".join(map(str,args))
        tags = "".join(f'[{value}]' for value in kwargs.values())
        print(f'[{self.trace_id}]{tags} - {msg}')

    def debug(self,*args,**kwargs):
        log_level=self.allowed_logs.get('debug')
        if self.log_level>log_level:
            return
        msg = " ".join(map(str,args))
        tags = "".join(f'[{value}]' for value in kwargs.values())
        print(f'[{self.trace_id}]{tags} - {msg}')

    def error(self,*args,**kwargs):
        log_level=self.allowed_logs.get('error')
        if self.log_level>log_level:
            return
        msg = " ".join(map(str,args))
        tags = "".join(f'[{value}]' for value in kwargs.values())
        print(f'[{self.trace_id}]{tags} - {msg}')

    