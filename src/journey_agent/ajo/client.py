import httpx
from tenacity import retry,stop_after_attempt,wait_exponential
from ..config import settings
class AJOClient:
    def headers(self):
        return {"Authorization":f"Bearer {settings.ajo_access_token}","x-api-key":settings.ajo_api_key,
        "x-gw-ims-org-id":settings.ajo_org_id,"x-sandbox-name":settings.ajo_sandbox,"Content-Type":"application/json"}
    @retry(stop=stop_after_attempt(3),wait=wait_exponential(min=1,max=8))
    async def request(self,method,path,**kw):
        async with httpx.AsyncClient(base_url=settings.ajo_base_url,timeout=30) as c:
            r=await c.request(method,path,headers=self.headers(),**kw); r.raise_for_status()
            return r.json() if r.content else {}
    async def list_journeys(self):
        # Verify current licensed AJO endpoint before production use.
        return await self.request("GET","/journey/authoring/journeys")
    async def create_journey(self,payload):
        return await self.request("POST","/journey/authoring/journeys",json=payload)
