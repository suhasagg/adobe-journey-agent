from ..models import Result
from ..llm import model
class AnalyzeAgent:
    async def run(self,s,c):
        r=await model().ainvoke("Analyze only supplied journey evidence. Identify funnel drop-offs, branch behavior, channel performance, latency, conversion and data gaps. Do not invent metrics. Goal:"+s.objective+" Evidence:"+repr(c.get("evidence",[])))
        return Result(step_id=s.id,status="ok",data={"analysis":r.content})
