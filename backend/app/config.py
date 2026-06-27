from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache
import os


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "RateEverything API"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://rateeverything:rateeverything@localhost:5432/rateeverything"
    database_url_sync: str = "postgresql+psycopg2://rateeverything:rateeverything@localhost:5432/rateeverything"

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    @property
    def deepseek_api_key_from_file(self) -> str:
        """Read DeepSeek API key from file if not set via env"""
        if self.deepseek_api_key:
            return self.deepseek_api_key
        try:
            key_path = os.path.expanduser("~/.deepseek_api_key")
            with open(key_path) as f:
                return f.read().strip()
        except (FileNotFoundError, IOError):
            return ""


@lru_cache()
def get_settings() -> Settings:
    return Settings()
