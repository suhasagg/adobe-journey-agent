from ..models import Result
class PublishAgent:
    async def run(self,s,c):
        spec=c.get("journey_spec")
        if not spec: return Result(step_id=s.id,status="failed",data={"reason":"missing journey specification"})
        if not c.get("approved"): return Result(step_id=s.id,status="needs_approval",data={"proposal":spec})
        # Adapter executes only after deterministic approval boundary.
        created=await c["repo"].create(spec)
        return Result(step_id=s.id,status="ok",data={"created":created})
