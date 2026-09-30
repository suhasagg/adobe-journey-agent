from langgraph.graph import StateGraph,START,END
from langgraph.checkpoint.memory import MemorySaver
from .models import State,Plan,Principal
from .planner import make_plan
from .memory.manager import memory
from .security.policy import authorize
from .agents.registry import AGENTS
from .ajo.repository import JourneyRepository
async def recall(s):
    p=Principal(**s["principal"]); memory.working(p.tenant_id,p.user_id,s["thread_id"],"user",s["goal"])
    return {"memories":memory.recall(p.tenant_id,p.user_id,s["goal"])}
async def plan(s): return {"plan":(await make_plan(s["goal"])).model_dump(),"results":{}}
def context_from(results,s):
    ctx={"repo":JourneyRepository(),"approved":s.get("approved",False),"evidence":s.get("evidence",[]),
         "journey_policy":s.get("journey_policy",{}),"simulation_population":s.get("simulation_population",[])}
    for v in results.values():
        if "journey_spec" in v.get("data",{}): ctx["journey_spec"]=v["data"]["journey_spec"]
    return ctx
async def execute(s):
    p=Principal(**s["principal"]); pl=Plan(**s["plan"]); results=dict(s.get("results",{}))
    for step in pl.steps:
        if step.id in results or any(d not in results or results[d]["status"]!="ok" for d in step.depends_on): continue
        dec=authorize(p,step)
        if dec["approval_required"] and not s.get("approved"): return {"pending_step":step.id,"results":results}
        r=await AGENTS[step.capability].run(step,context_from(results,s)); results[step.id]=r.model_dump()
        memory.episodic(p.tenant_id,p.user_id,f"{step.capability}: {step.objective}; status={r.status}",{"run_id":s["run_id"],"step_id":step.id})
    return {"results":results,"pending_step":None}
def route(s): return "approval" if s.get("pending_step") else "finish"
async def approval(s): return {}
async def finish(s):
    p=Principal(**s["principal"]); text="Journey workflow results: "+repr(s.get("results",{}))
    memory.working(p.tenant_id,p.user_id,s["thread_id"],"assistant",text)
    memory.procedural(p.tenant_id,p.user_id,"Successful journey workflow: "+s["goal"],{"run_id":s["run_id"]})
    return {"final":text}
g=StateGraph(State)
for n,f in [("recall",recall),("plan",plan),("execute",execute),("approval",approval),("finish",finish)]: g.add_node(n,f)
g.add_edge(START,"recall"); g.add_edge("recall","plan"); g.add_edge("plan","execute")
g.add_conditional_edges("execute",route,{"approval":"approval","finish":"finish"}); g.add_edge("approval",END); g.add_edge("finish",END)
graph=g.compile(checkpointer=MemorySaver())
