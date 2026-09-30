import pytest
from journey_agent.agents.simulate import SimulationAgent
from journey_agent.models import Step
@pytest.mark.asyncio
async def test_structural_simulation():
    s=Step(id="x",capability="simulate",objective="test")
    r=await SimulationAgent().run(s,{"journey_spec":{"nodes":[{"id":"start"}]},"simulation_population":[1,2]})
    assert r.data["structural_valid"] and r.data["sample_population"]==2
