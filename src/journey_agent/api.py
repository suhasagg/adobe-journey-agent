import uuid
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from .graph import graph
app=FastAPI(title="Adobe Journey Agent clean-room production reference")
class Req(BaseModel): goal:str; tenant_id:str; user_id:str; permissions:set[str]
@app.get("/healthz")
async def health(): return {"ok":True}
@app.post("/v1/journey-agent/runs")
async def run(x:Req):
    rid,tid=str(uuid.uuid4()),str(uuid.uuid4())
    s={"run_id":rid,"thread_id":tid,"goal":x.goal,"principal":{"tenant_id":x.tenant_id,"user_id":x.user_id,"permissions":x.permissions}}
    try: return await graph.ainvoke(s,config={"configurable":{"thread_id":tid}})
    except PermissionError as e: raise HTTPException(403,str(e))
