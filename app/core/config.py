from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # App
    APP_TITLE: str = "Lab Scheduling API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://lab_user:lab_pass@db:5432/lab_db"

    # API Keys
    API_KEY_AGENT: str = "agent-key-change-in-prod"
    API_KEY_ADMIN: str = "admin-key-change-in-prod"

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


settings = Settings()
