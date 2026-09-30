from ..models import Result
from ..llm import model
class OptimizeAgent:
    async def run(self,s,c):
        r=await model().ainvoke("Optimize only from supplied evidence. Consider drop-off, channel effectiveness, wait duration, frequency, fatigue, consent, conversion, holdout and measurement. State uncertainty. Goal:"+s.objective+" Evidence:"+repr(c.get("evidence",[])))
        return Result(step_id=s.id,status="ok",data={"recommendation":r.content})
