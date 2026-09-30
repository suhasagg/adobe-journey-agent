from ..models import Result,JourneySpec
from ..llm import model
class DesignAgent:
    async def run(self,s,c):
        spec=await model().with_structured_output(JourneySpec).ainvoke(
        "Design a safe multi-step customer journey. Include entry, conditions, actions, waits, exits and KPIs. "
        "Respect consent/frequency caps from evidence. Unknown physical IDs must remain unresolved. Goal:"+s.objective+
        " Evidence:"+repr(c.get("evidence",[])))
        return Result(step_id=s.id,status="ok",data={"journey_spec":spec.model_dump()})
