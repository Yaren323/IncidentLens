from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./incidentlens-dev.db"
    ai_enabled: bool = False
    ollama_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "qwen3:4b-instruct"
    max_log_bytes: int = 262144
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
