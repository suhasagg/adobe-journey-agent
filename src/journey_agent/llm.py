from langchain_openai import ChatOpenAI
from .config import settings
def model(temp=0): return ChatOpenAI(model=settings.llm_model,temperature=temp)
