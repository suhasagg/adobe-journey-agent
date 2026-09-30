from journey_agent.memory.manager import memory
def test_tenant_isolation():
    memory.semantic("t1","u","quiet hours start at 21:00")
    assert memory.recall("t2","u","quiet hours")==[]
