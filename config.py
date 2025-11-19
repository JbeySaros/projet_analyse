from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Data Analysis Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL: int = 3600
    CACHE_ENABLED: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE_MAX_BYTES: int = 10485760
    LOG_FILE_BACKUP_COUNT: int = 5

    # Data Processing
    MAX_FILE_SIZE: int = 104857600
    CHUNK_SIZE: int = 10000
    CSV_ENCODING: str = "utf-8"
    CSV_DELIMITER: str = ","

    # Statistics
    OUTLIER_METHOD: str = "iqr"
    OUTLIER_THRESHOLD: float = 1.5
    ZSCORE_THRESHOLD: float = 3.0

    # Visualization
    CHART_THEME: str = "plotly"
    CHART_WIDTH: int = 1200
    CHART_HEIGHT: int = 600

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Rate Limiting
    RATE_LIMIT: str = "100/minute"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
