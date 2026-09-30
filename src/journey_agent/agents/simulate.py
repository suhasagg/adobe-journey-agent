from ..models import Result
class SimulationAgent:
    async def run(self,s,c):
        spec=c.get("journey_spec") or {}
        population=c.get("simulation_population",[])
        # Deterministic structural simulation; production connects to governed profile/event simulator.
        nodes={n.get("id"):n for n in spec.get("nodes",[])}
        return Result(step_id=s.id,status="ok",data={"structural_valid":bool(nodes),"sample_population":len(population),
        "warning":"Outcome simulation requires authoritative profile/event distributions; no conversion metrics fabricated."})
