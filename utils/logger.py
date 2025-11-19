"""
Module de logging professionnel avec rotation de fichiers.
Implémente un Singleton pour garantir une seule instance du logger.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from config import settings


class LoggerManager:
    """
    Gestionnaire de logging Singleton.
    Centralise la configuration des loggers pour toute l'application.
    """
    
    _instance: Optional["LoggerManager"] = None
    _loggers: dict[str, logging.Logger] = {}
    
    def __new__(cls):
        """Implémentation du pattern Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialise le gestionnaire de logging."""
        if self._initialized:
            return
        
        self._initialized = True
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """Configure le logger racine."""
        root_logger = logging.getLogger()
        root_logger.setLevel(settings.LOG_LEVEL)
        
        # Supprime les handlers existants pour éviter les doublons
        root_logger.handlers.clear()
    
    def get_logger(
        self,
        name: str,
        log_file: Optional[str] = None,
        console: bool = True
    ) -> logging.Logger:
        """
        Récupère ou crée un logger configuré.
        
        Args:
            name: Nom du logger (généralement __name__ du module)
            log_file: Nom du fichier de log (optionnel)
            console: Active la sortie console
            
        Returns:
            logging.Logger: Logger configuré
            
        Example:
            >>> logger = LoggerManager().get_logger(__name__)
            >>> logger.info("Message d'information")
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(settings.LOG_LEVEL)
        logger.propagate = False
        
        # Formatter
        formatter = logging.Formatter(
            settings.LOG_FORMAT,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Console Handler
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(settings.LOG_LEVEL)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File Handler avec rotation
        if log_file:
            file_path = settings.LOG_DIR / log_file
            file_handler = RotatingFileHandler(
                file_path,
                maxBytes=settings.LOG_FILE_MAX_BYTES,
                backupCount=settings.LOG_FILE_BACKUP_COUNT,
                encoding="utf-8"
            )
            file_handler.setLevel(settings.LOG_LEVEL)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        else:
            # Log général dans app.log par défaut
            default_file = settings.LOG_DIR / "app.log"
            file_handler = RotatingFileHandler(
                default_file,
                maxBytes=settings.LOG_FILE_MAX_BYTES,
                backupCount=settings.LOG_FILE_BACKUP_COUNT,
                encoding="utf-8"
            )
            file_handler.setLevel(settings.LOG_LEVEL)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        self._loggers[name] = logger
        return logger
    
    @staticmethod
    def create_module_logger(module_name: str) -> logging.Logger:
        """
        Factory method pour créer rapidement un logger pour un module.
        
        Args:
            module_name: Nom du module (utilisez __name__)
            
        Returns:
            logging.Logger: Logger configuré pour le module
            
        Example:
            >>> logger = LoggerManager.create_module_logger(__name__)
        """
        manager = LoggerManager()
        log_file = f"{module_name.replace('.', '_')}.log"
        return manager.get_logger(module_name, log_file=log_file)


class PerformanceLogger:
    """
    Context manager pour logger les performances d'une opération.
    
    Example:
        >>> with PerformanceLogger(logger, "load_csv"):
        ...     df = pd.read_csv("data.csv")
    """
    
    def __init__(self, logger: logging.Logger, operation: str):
        """
        Initialise le performance logger.
        
        Args:
            logger: Logger à utiliser
            operation: Nom de l'opération à tracer
        """
        self.logger = logger
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        """Démarre le chronomètre."""
        import time
        self.start_time = time.time()
        self.logger.info(f"Début de l'opération: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Arrête le chronomètre et log le temps écoulé."""
        import time
        elapsed = time.time() - self.start_time
        
        if exc_type is not None:
            self.logger.error(
                f"Échec de l'opération '{self.operation}' après {elapsed:.2f}s",
                exc_info=True
            )
        else:
            self.logger.info(
                f"Fin de l'opération '{self.operation}' en {elapsed:.2f}s"
            )
        
        return False  # Ne pas supprimer l'exception


def log_function_call(logger: logging.Logger):
    """
    Décorateur pour logger automatiquement les appels de fonction.
    
    Args:
        logger: Logger à utiliser
        
    Example:
        >>> @log_function_call(logger)
        ... def my_function(x, y):
        ...     return x + y
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(
                f"Appel de {func.__name__} avec args={args}, kwargs={kwargs}"
            )
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} terminé avec succès")
                return result
            except Exception as e:
                logger.error(
                    f"Erreur dans {func.__name__}: {str(e)}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


# Instance globale pour faciliter l'utilisation
logger_manager = LoggerManager()


# Helper function pour usage rapide
def get_logger(name: str) -> logging.Logger:
    """
    Fonction helper pour obtenir rapidement un logger.
    
    Args:
        name: Nom du logger (utilisez __name__)
        
    Returns:
        logging.Logger: Logger configuré
        
    Example:
        >>> from utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Mon message")
    """
    return logger_manager.get_logger(name)
