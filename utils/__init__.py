"""
Module utils - Utilitaires partagés.

Ce module contient les outils transverses utilisés par tous les autres modules.

Composants:
    - Logger: Système de logging professionnel avec rotation
    - PerformanceLogger: Context manager pour mesurer les performances
    - LoggerManager: Singleton pour gérer les loggers

Usage:
    >>> from utils.logger import get_logger, PerformanceLogger
    >>> 
    >>> logger = get_logger(__name__)
    >>> logger.info("Message d'information")
    >>> 
    >>> # Mesure de performance
    >>> with PerformanceLogger(logger, "operation"):
    ...     # Code à mesurer
    ...     process_data()
"""

__version__ = "1.0.0"
__author__ = "Data Analysis Team"

from utils.logger import (
    get_logger,
    LoggerManager,
    PerformanceLogger,
    log_function_call
)

__all__ = [
    "get_logger",
    "LoggerManager",
    "PerformanceLogger",
    "log_function_call",
]
