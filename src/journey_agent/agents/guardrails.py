from ..models import Result
class GuardrailAgent:
    async def run(self,s,c):
        policy=c.get("journey_policy",{})
        checks={"consent_required":policy.get("consent_required",True),
                "frequency_cap":policy.get("frequency_cap"),
                "quiet_hours":policy.get("quiet_hours"),
                "max_duration_days":policy.get("max_duration_days",30)}
        return Result(step_id=s.id,status="ok",data={"guardrails":checks})
