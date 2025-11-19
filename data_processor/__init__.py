"""
Module data_processor - Couche de traitement des données.

Ce module contient tous les outils pour transformer, nettoyer, agréger
et analyser les données chargées.

Classes principales:
    - DataCleaner: Nettoyage avancé (outliers, imputation, normalisation)
    - DataAggregator: Agrégations complexes et calcul de KPIs
    - StatisticsCalculator: Statistiques descriptives et inférentielles

Enums:
    - ImputationStrategy: Stratégies d'imputation des valeurs manquantes
    - ScalingMethod: Méthodes de normalisation

Usage:
    >>> from data_processor import DataCleaner, DataAggregator
    >>> 
    >>> # Nettoyage
    >>> cleaner = DataCleaner()
    >>> df_clean = cleaner.clean(df, remove_outliers=True)
    >>> 
    >>> # Agrégations
    >>> aggregator = DataAggregator()
    >>> kpis = aggregator.calculate_kpis(df_clean)
    >>> sales_by_cat = aggregator.calculate_sales_by_category(df_clean)
"""

__version__ = "1.0.0"
__author__ = "Data Analysis Team"

# Imports
from data_processor.cleaner import (
    DataCleaner,
    ImputationStrategy,
    ScalingMethod
)

from data_processor.aggregator import (
    DataAggregator
)

from data_processor.statistics import (
    StatisticsCalculator,
    StatisticalSummary
)

__all__ = [
    # Cleaner
    "DataCleaner",
    "ImputationStrategy",
    "ScalingMethod",
    
    # Aggregator
    "DataAggregator",
    
    # Statistics
    "StatisticsCalculator",
    "StatisticalSummary",
]
