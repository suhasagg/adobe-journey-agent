import pytest
from journey_agent.models import Principal,Step
from journey_agent.security.policy import authorize,Denied
def test_publish_approval():
    p=Principal(tenant_id="t",user_id="u",permissions={"manage_journeys"})
    assert authorize(p,Step(id="1",capability="publish",objective="x",write=True))["approval_required"]
def test_denied():
    with pytest.raises(Denied): authorize(Principal(tenant_id="t",user_id="u"),Step(id="1",capability="inventory",objective="x"))
