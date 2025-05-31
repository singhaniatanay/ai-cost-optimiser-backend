from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    model_timeout_s: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings() 