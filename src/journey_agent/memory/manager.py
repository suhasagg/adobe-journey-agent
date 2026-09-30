from .store import store
class Memory:
    def working(self,t,u,thread,role,text): store.work(f"{t}:{u}:{thread}",role,text)
    def episodic(self,t,u,text,meta=None): return store.put(t,u,"episodic",text,meta,180*86400,.7)
    def semantic(self,t,u,text,meta=None): return store.put(t,u,"semantic",text,meta,365*86400,.8)
    def procedural(self,t,u,text,meta=None): return store.put(t,u,"procedural",text,meta,None,.9)
    def recall(self,t,u,q): return store.search(t,u,q)
memory=Memory()
