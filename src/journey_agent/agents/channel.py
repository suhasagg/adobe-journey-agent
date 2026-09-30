from ..models import Result
from ..llm import model
class ChannelAgent:
    async def run(self,s,c):
        r=await model().ainvoke("Choose channel/action strategy only from eligibility, consent, preferences and evidence. Include fallback and suppression. Never invent consent. Goal:"+s.objective+" Evidence:"+repr(c.get("evidence",[])))
        return Result(step_id=s.id,status="ok",data={"channel_plan":r.content})
