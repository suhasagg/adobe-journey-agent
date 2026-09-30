from ..models import Result
class InventoryAgent:
    async def run(self,s,c):
        x=await c["repo"].inventory()
        return Result(step_id=s.id,status="ok",data={"journeys":x[:200],"count":len(x)})
