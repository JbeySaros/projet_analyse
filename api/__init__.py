"""
Module api - API REST FastAPI.

Ce module expose l'ensemble des fonctionnalités via une API REST.

Endpoints principaux:
    - POST /api/v1/upload         : Upload de fichiers CSV/Excel
    - POST /api/v1/analyze        : Analyse complète des données
    - POST /api/v1/charts/*       : Création de graphiques
    - POST /api/v1/reports/*      : Génération de rapports
    - POST /api/v1/stats/*        : Calculs statistiques
    - GET  /health                : Health check
    - GET  /api/docs              : Documentation Swagger

Features:
    - Rate limiting (SlowAPI)
    - CORS configuré
    - Validation Pydantic
    - Dependency Injection
    - Gestion d'erreurs globale
    - Documentation auto (Swagger/ReDoc)

Usage:
    # Démarrer l'API
    >>> uvicorn api.main:app --reload
    
    # Ou
    >>> python api/main.py
    
    # Accéder à la doc
    >>> http://localhost:8000/api/docs
"""

__version__ = "1.0.0"
__author__ = "Data Analysis Team"

from api.main import app

__all__ = ["app"]
