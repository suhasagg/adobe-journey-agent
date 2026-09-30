from .client import AJOClient
class JourneyRepository:
    def __init__(self,client=None): self.client=client or AJOClient()
    async def inventory(self):
        x=await self.client.list_journeys()
        if isinstance(x,list): return x
        return x.get("items",x.get("journeys",[]))
    async def create(self,payload): return await self.client.create_journey(payload)
