"""Configuration centralisée de l'application."""
import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Configuration principale."""
    
    APP_NAME: str = "Data Analysis Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    LOG_DIR: Path = BASE_DIR / "logs"
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_URL: str = ""
    
    @validator("REDIS_URL", pre=True, always=True)
    def assemble_redis_url(cls, v, values):
        if v:
            return v
        password = values.get("REDIS_PASSWORD")
        auth = f":{password}@" if password else ""
        return f"redis://{auth}{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"
    
    CACHE_TTL: int = 3600
    CACHE_ENABLED: bool = True
    
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_FILE_BACKUP_COUNT: int = 5
    
    MAX_FILE_SIZE: int = 100 * 1024 * 1024
    CHUNK_SIZE: int = 10000
    ALLOWED_EXTENSIONS: set[str] = {"csv", "xlsx", "xls"}
    
    CSV_ENCODING: str = "utf-8"
    CSV_DELIMITER: str = ","
    
    OUTLIER_METHOD: Literal["iqr", "zscore"] = "iqr"
    OUTLIER_THRESHOLD: float = 1.5
    
    CHART_THEME: str = "plotly"
    CHART_WIDTH: int = 1200
    CHART_HEIGHT: int = 600
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    RATE_LIMIT: str = "100/minute"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._create_directories()
    
    def _create_directories(self):
        for directory in [self.DATA_DIR, self.UPLOAD_DIR, self.OUTPUT_DIR, self.LOG_DIR]:
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()


def get_settings() -> Settings:
    return settings
