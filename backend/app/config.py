from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    youcam_api_key: str
    youcam_api_base: str = "https://yce-api-01.makeupar.com"

    deepseek_api_key: str
    deepseek_model_id: str = "deepseek-chat"

    public_base_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000"


settings = Settings()
