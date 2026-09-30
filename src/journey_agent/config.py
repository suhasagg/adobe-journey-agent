from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file=".env",extra="ignore")
    llm_model:str="gpt-4.1"; ajo_base_url:str="https://platform.adobe.io"
    ajo_access_token:str=""; ajo_api_key:str=""; ajo_org_id:str=""; ajo_sandbox:str="prod"
settings=Settings()
