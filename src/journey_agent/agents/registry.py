from .inventory import InventoryAgent
from .analyze import AnalyzeAgent
from .design import DesignAgent
from .simulate import SimulationAgent
from .optimize import OptimizeAgent
from .channel import ChannelAgent
from .guardrails import GuardrailAgent
from .publish import PublishAgent
AGENTS={"inventory":InventoryAgent(),"analyze":AnalyzeAgent(),"design":DesignAgent(),
"simulate":SimulationAgent(),"optimize":OptimizeAgent(),"channel":ChannelAgent(),
"guardrails":GuardrailAgent(),"publish":PublishAgent()}
