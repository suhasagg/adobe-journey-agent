from .llm import model
from .models import Plan
async def make_plan(goal):
    return await model().with_structured_output(Plan).ainvoke(
    "Build a minimal safe Journey Agent DAG using inventory,analyze,design,simulate,optimize,channel,guardrails,publish. "
    "publish is the only write capability. Dependencies reference earlier IDs. Goal:"+goal)
