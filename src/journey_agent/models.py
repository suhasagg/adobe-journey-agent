from typing import Any,Literal,TypedDict
from pydantic import BaseModel,Field
class Principal(BaseModel):
    tenant_id:str; user_id:str; permissions:set[str]=set()
class Step(BaseModel):
    id:str
    capability:Literal["inventory","analyze","design","simulate","optimize","channel","guardrails","publish"]
    objective:str; depends_on:list[str]=Field(default_factory=list); write:bool=False
class Plan(BaseModel): goal:str; steps:list[Step]
class Result(BaseModel):
    step_id:str; status:Literal["ok","failed","needs_approval"]; data:dict[str,Any]=Field(default_factory=dict)
class JourneyNode(BaseModel):
    id:str; kind:Literal["entry","condition","action","wait","exit"]; config:dict[str,Any]=Field(default_factory=dict)
class JourneyEdge(BaseModel): source:str; target:str; condition:str|None=None
class JourneySpec(BaseModel):
    name:str; description:str; entry_criteria:str; nodes:list[JourneyNode]; edges:list[JourneyEdge]
    exit_criteria:list[str]=Field(default_factory=list); kpis:list[str]=Field(default_factory=list)
class State(TypedDict,total=False):
    run_id:str; thread_id:str; principal:dict; goal:str; plan:dict; results:dict
    memories:list[dict]; pending_step:str|None; approved:bool; final:str
