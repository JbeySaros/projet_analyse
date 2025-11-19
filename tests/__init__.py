"""
Module tests - Suite de tests.

Ce module contient tous les tests unitaires et d'intégration.

Structure:
    - test_loader.py       : Tests du data_loader
    - test_processor.py    : Tests du data_processor
    - test_visualization.py: Tests de visualization
    - test_api.py          : Tests de l'API REST

Markers pytest:
    - @pytest.mark.unit         : Tests unitaires
    - @pytest.mark.integration  : Tests d'intégration
    - @pytest.mark.api          : Tests API
    - @pytest.mark.slow         : Tests lents
    - @pytest.mark.requires_redis : Tests nécessitant Redis

Usage:
    # Tous les tests
    >>> pytest
    
    # Tests unitaires seulement
    >>> pytest -m unit
    
    # Avec couverture
    >>> pytest --cov=data_loader --cov=data_processor
    
    # Tests API
    >>> pytest -m api -v
"""

__version__ = "1.0.0"
__author__ = "Data Analysis Team"
