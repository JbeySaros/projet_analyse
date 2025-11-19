"""
Configuration centralisée pour la plateforme d'analyse de données.
Utilise pydantic-settings pour la gestion des variables d'environnement.
"""
import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Configuration principale de l'application."""
    
    # Informations Générales
    APP_NAME: str = "Data Analysis Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    
    # Chemins
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    LOG_DIR: Path = BASE_DIR / "logs"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    API_WORKERS: int = 4
    
    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_URL: str = Field(default="")
    
    @validator("REDIS_URL", pre=True, always=True)
    def assemble_redis_url(cls, v, values):
        """Construit l'URL Redis à partir des composants."""
        if v:
            return v
        password = values.get("REDIS_PASSWORD")
        auth = f":{password}@" if password else ""
        return (
            f"redis://{auth}{values.get('REDIS_HOST')}:"
            f"{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"
        )
    
    # Cache Configuration
    CACHE_TTL: int = 3600  # 1 heure en secondes
    CACHE_ENABLED: bool = True
    
    # Logging Configuration
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: str = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(filename)s:%(lineno)d - %(message)s"
    )
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    LOG_FILE_BACKUP_COUNT: int = 5
    
    # Data Processing Configuration
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100 MB
    CHUNK_SIZE: int = 10000  # Lignes par chunk pour gros fichiers
    ALLOWED_EXTENSIONS: set[str] = {"csv", "xlsx", "xls"}
    
    # CSV Configuration
    CSV_ENCODING: str = "utf-8"
    CSV_DELIMITER: str = ","
    CSV_AUTO_DETECT_ENCODING: bool = True
    CSV_AUTO_DETECT_DELIMITER: bool = True
    
    # Data Validation
    MIN_DATA_ROWS: int = 1
    MAX_MISSING_PERCENTAGE: float = 0.5  # 50%
    
    # Statistics Configuration
    OUTLIER_METHOD: Literal["iqr", "zscore"] = "iqr"
    OUTLIER_THRESHOLD: float = 1.5  # Pour IQR
    ZSCORE_THRESHOLD: float = 3.0  # Pour Z-score
    
    # Visualization Configuration
    CHART_THEME: str = "plotly"
    CHART_WIDTH: int = 1200
    CHART_HEIGHT: int = 600
    CHART_DPI: int = 100  # Pour Matplotlib
    
    # Report Generation
    REPORT_FORMAT: Literal["html", "pdf", "both"] = "both"
    PDF_PAGE_SIZE: str = "A4"
    
    # Performance
    MAX_WORKERS: int = 4  # Pour le traitement parallèle
    ENABLE_PROFILING: bool = False
    
    # Rate Limiting
    RATE_LIMIT: str = "100/minute"
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Database (optionnel pour extension future)
    DATABASE_URL: str | None = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        """Initialise les settings et crée les répertoires nécessaires."""
        super().__init__(**kwargs)
        self._create_directories()
    
    def _create_directories(self):
        """Crée les répertoires nécessaires s'ils n'existent pas."""
        directories = [
            self.DATA_DIR,
            self.UPLOAD_DIR,
            self.OUTPUT_DIR,
            self.LOG_DIR,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_production(self) -> bool:
        """Vérifie si l'environnement est production."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Vérifie si l'environnement est développement."""
        return self.ENVIRONMENT == "development"


# Instance globale des settings (Singleton pattern)
settings = Settings()


# Configuration spécifique pour les tests
class TestSettings(Settings):
    """Configuration pour l'environnement de test."""
    
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    CACHE_ENABLED: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"
    
    model_config = SettingsConfigDict(
        env_file=".env.test",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


def get_settings() -> Settings:
    """
    Factory function pour obtenir les settings.
    Utile pour l'injection de dépendances dans FastAPI.
    
    Returns:
        Settings: Instance de configuration
    """
    return settings
