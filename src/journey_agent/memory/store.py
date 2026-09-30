import time,hashlib,re
from collections import defaultdict,deque
SECRET=re.compile(r"(token|password|api[_-]?key)\s*[:=]\s*\S+",re.I)
class Store:
    def __init__(self): self.working=defaultdict(lambda:deque(maxlen=40)); self.long={}
    def clean(self,x): return SECRET.sub(r"\1=[REDACTED]",x)[:18000]
    def work(self,key,role,text): self.working[key].append({"role":role,"text":self.clean(text)})
    def put(self,t,u,kind,text,meta=None,ttl=None,importance=.5):
        text=self.clean(text); mid=hashlib.sha256(f"{t}{u}{kind}{text}{time.time_ns()}".encode()).hexdigest()[:24]
        self.long[mid]={"id":mid,"tenant":t,"user":u,"kind":kind,"text":text,"meta":meta or {},
        "importance":importance,"expires":time.time()+ttl if ttl else None}; return self.long[mid]
    def search(self,t,u,q,n=8):
        words=set(q.lower().split()); now=time.time(); out=[]
        for m in self.long.values():
            if m["tenant"]!=t or m["user"]!=u or (m["expires"] and m["expires"]<now): continue
            overlap=len(words & set(m["text"].lower().split()))/(len(words) or 1)
            score=.75*overlap+.25*m["importance"]
            if score: out.append((score,m))
        return [m for _,m in sorted(out,key=lambda x:x[0],reverse=True)[:n]]
store=Store()
