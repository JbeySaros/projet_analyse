"""
API REST FastAPI pour la plateforme d'analyse de données.
Point d'entrée principal de l'API.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Optional, List
from pathlib import Path
import pandas as pd
import tempfile
from datetime import datetime

from config import settings, get_settings
from utils.logger import get_logger
from utils.cache import cache, cached, cache_analysis_result, get_cache_stats
from data_loader.csv_loader import DataLoaderRepository
from data_loader.data_validator import DataValidator
from data_processor.cleaner import DataCleaner
from data_processor.aggregator import DataAggregator
from data_processor.statistics import StatisticsCalculator
from visualization.chart_builder import ChartBuilder
from visualization.report_generator import ReportGenerator


logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialisation FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API REST pour l'analyse de données de ventes",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Dépendances réutilisables
def get_data_loader():
    """Dependency pour le DataLoader."""
    return DataLoaderRepository()

def get_validator():
    """Dependency pour le DataValidator."""
    return DataValidator()

def get_cleaner():
    """Dependency pour le DataCleaner."""
    return DataCleaner()

def get_aggregator():
    """Dependency pour le DataAggregator."""
    return DataAggregator()

def get_stats_calc():
    """Dependency pour le StatisticsCalculator."""
    return StatisticsCalculator()

def get_chart_builder():
    """Dependency pour le ChartBuilder."""
    return ChartBuilder()

def get_report_generator():
    """Dependency pour le ReportGenerator."""
    return ReportGenerator()


# ====================
# ROUTES DE L'API
# ====================

@app.get("/")
async def root():
    """Route racine - informations de l'API."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "docs": "/api/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    cache_stats = get_cache_stats()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cache": cache_stats
    }


# ====================
# ROUTES D'UPLOAD
# ====================

@app.post(f"{settings.API_PREFIX}/upload")
@limiter.limit(settings.RATE_LIMIT)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    validate: bool = Query(True, description="Valider les données"),
    loader: DataLoaderRepository = Depends(get_data_loader),
    validator: DataValidator = Depends(get_validator)
):
    """
    Upload et charge un fichier CSV/Excel.

    Args:
        file: Fichier à uploader
        validate: Effectuer la validation

    Returns:
        JSON avec informations sur les données chargées
    """
    logger.info(f"Upload fichier: {file.filename}")

    # Vérification de l'extension
    file_ext = Path(file.filename).suffix.lower().lstrip('.')
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté: {file_ext}. Formats autorisés: {settings.ALLOWED_EXTENSIONS}"
        )

    try:
        # Sauvegarder temporairement le fichier
        temp_path = settings.UPLOAD_DIR / f"temp_{datetime.now().timestamp()}_{file.filename}"

        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Charger les données
        df = loader.load_data(temp_path)

        # Validation optionnelle
        validation_result = None
        if validate and file_ext == 'csv':
            validation_result = validator.validate_sales_data(df)

        # Informations à retourner
        response = {
            "success": True,
            "filename": file.filename,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "memory_mb": float(df.memory_usage(deep=True).sum() / (1024**2)),
            "validation": {
                "is_valid": validation_result.is_valid if validation_result else None,
                "errors": validation_result.errors if validation_result else [],
                "warnings": validation_result.warnings if validation_result else []
            } if validation_result else None
        }

        logger.info(f"Fichier chargé avec succès: {len(df)} lignes")
        return response

    except Exception as e:
        logger.error(f"Erreur lors de l'upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Nettoyage
        if temp_path.exists():
            temp_path.unlink()


# ====================
# ROUTES D'ANALYSE
# ====================

@app.post(f"{settings.API_PREFIX}/analyze")
@limiter.limit(settings.RATE_LIMIT)
async def analyze_data(
    request: Request,
    file: UploadFile = File(...),
    clean: bool = Query(True, description="Nettoyer les données"),
    remove_outliers: bool = Query(False, description="Supprimer les outliers"),
    use_cache: bool = Query(True, description="Utiliser le cache Redis"),
    loader: DataLoaderRepository = Depends(get_data_loader),
    cleaner: DataCleaner = Depends(get_cleaner),
    aggregator: DataAggregator = Depends(get_aggregator),
    stats_calc: StatisticsCalculator = Depends(get_stats_calc)
):
    """
    Analyse complète d'un fichier de données avec cache Redis.

    Returns:
        JSON avec KPIs, statistiques et agrégations
    """
    logger.info(f"Analyse des données: {file.filename}")

    temp_path = None
    try:
        # Calculer le hash du fichier pour le cache
        content = await file.read()
        import hashlib
        file_hash = hashlib.md5(content).hexdigest()

        # Vérifier le cache si activé
        if use_cache and cache.is_available:
            cache_key = f"analysis:{file_hash}:full"
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"✓ Résultat d'analyse en cache pour {file.filename}")
                return cached_result

        # Sauvegarder et charger
        temp_path = settings.UPLOAD_DIR / f"analyze_{datetime.now().timestamp()}_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(content)

        df = loader.load_data(temp_path)

        # Nettoyage optionnel
        if clean:
            df = cleaner.clean(df, remove_outliers=remove_outliers, impute_missing=True)

        # Calculs avec cache par sous-partie
        if use_cache and cache.is_available:
            @cache_analysis_result(file_hash, "kpis")
            def get_kpis():
                return aggregator.calculate_kpis(df)

            @cache_analysis_result(file_hash, "by_category")
            def get_by_category():
                return aggregator.calculate_sales_by_category(df).to_dict('records')

            @cache_analysis_result(file_hash, "by_city")
            def get_by_city():
                return aggregator.calculate_sales_by_city(df).to_dict('records')

            @cache_analysis_result(file_hash, "top_products")
            def get_top_products():
                return aggregator.calculate_top_products(df, top_n=10).to_dict('records')

            @cache_analysis_result(file_hash, "stats")
            def get_stats():
                return stats_calc.generate_statistics_report(df)

            kpis = get_kpis()
            sales_by_category = get_by_category()
            sales_by_city = get_by_city()
            top_products = get_top_products()
            stats_report = get_stats()
        else:
            kpis = aggregator.calculate_kpis(df)
            sales_by_category = aggregator.calculate_sales_by_category(df).to_dict('records')
            sales_by_city = aggregator.calculate_sales_by_city(df).to_dict('records')
            top_products = aggregator.calculate_top_products(df, top_n=10).to_dict('records')
            stats_report = stats_calc.generate_statistics_report(df)

        response = {
            "success": True,
            "data_info": {
                "rows": len(df),
                "columns": len(df.columns)
            },
            "kpis": kpis,
            "sales_by_category": sales_by_category,
            "sales_by_city": sales_by_city,
            "top_products": top_products,
            "statistics": stats_report,
            "cached": False
        }

        # Mettre en cache le résultat complet
        if use_cache and cache.is_available:
            cache_key = f"analysis:{file_hash}:full"
            cache.set(cache_key, response, ttl=settings.CACHE_TTL)
            logger.info(f"✓ Résultat mis en cache: {cache_key}")

        logger.info("Analyse terminée avec succès")
        return response

    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


# ====================
# ROUTES DE VISUALISATION
# ====================

@app.post(f"{settings.API_PREFIX}/charts/bar")
@limiter.limit(settings.RATE_LIMIT)
async def create_bar_chart(
    request: Request,
    file: UploadFile = File(...),
    x: str = Query(..., description="Colonne X"),
    y: str = Query(..., description="Colonne Y"),
    title: str = Query("Bar Chart", description="Titre du graphique"),
    loader: DataLoaderRepository = Depends(get_data_loader),
    chart_builder: ChartBuilder = Depends(get_chart_builder)
):
    """
    Crée un graphique en barres et le retourne en HTML.
    """
    temp_path = None
    try:
        temp_path = settings.UPLOAD_DIR / f"chart_{datetime.now().timestamp()}_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        df = loader.load_data(temp_path)

        # Agrégation si nécessaire
        if df[x].dtype == 'object':
            df = df.groupby(x)[y].sum().reset_index()

        fig = chart_builder.create_bar_chart(df, x=x, y=y, title=title)

        # Retourner le HTML du graphique
        html = fig.to_html(include_plotlyjs='cdn')

        return {"success": True, "html": html}

    except Exception as e:
        logger.error(f"Erreur création graphique: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


# ====================
# ROUTES DE RAPPORTS
# ====================

@app.post(f"{settings.API_PREFIX}/reports/generate")
@limiter.limit("10/hour")  # Limite plus stricte pour les rapports
async def generate_report(
    request: Request,
    file: UploadFile = File(...),
    format: str = Query("html", regex="^(html|pdf)$"),
    loader: DataLoaderRepository = Depends(get_data_loader),
    report_gen: ReportGenerator = Depends(get_report_generator)
):
    """
    Génère un rapport complet d'analyse.
    Args:
        format: Format du rapport ('html' ou 'pdf')

    Returns:
        Fichier du rapport généré
    """
    logger.info(f"Génération de rapport ({format}): {file.filename}")

    temp_input = None
    temp_output = None

    try:
        # Charger les données
        temp_input = settings.UPLOAD_DIR / f"report_input_{datetime.now().timestamp()}_{file.filename}"
        with open(temp_input, "wb") as f:
            f.write(await file.read())

        df = loader.load_data(temp_input)

        # Générer le rapport
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"rapport_analyse_{timestamp}.{format}"
        temp_output = settings.OUTPUT_DIR / output_filename

        report_path = report_gen.generate_sales_report(
            df,
            output_path=str(temp_output),
            format=format,
            include_charts=True
        )

        logger.info(f"Rapport généré: {report_path}")

        # Retourner le fichier
        return FileResponse(
            path=report_path,
            filename=output_filename,
            media_type='application/pdf' if format == 'pdf' else 'text/html'
        )

    except Exception as e:
        logger.error(f"Erreur génération rapport: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_input and temp_input.exists():
            temp_input.unlink()


# ====================
# ROUTES DE STATISTIQUES
# ====================

@app.post(f"{settings.API_PREFIX}/stats/describe")
@limiter.limit(settings.RATE_LIMIT)
async def describe_statistics(
    request: Request,
    file: UploadFile = File(...),
    loader: DataLoaderRepository = Depends(get_data_loader),
    stats_calc: StatisticsCalculator = Depends(get_stats_calc)
):
    """
    Retourne les statistiques descriptives complètes.
    """
    temp_path = None
    try:
        temp_path = settings.UPLOAD_DIR / f"stats_{datetime.now().timestamp()}_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        df = loader.load_data(temp_path)

        # Calcul des statistiques
        stats_dict = stats_calc.describe_dataframe(df)

        # Conversion en format JSON-friendly
        result = {
            col: stats.to_dict()
            for col, stats in stats_dict.items()
        }

        return {"success": True, "statistics": result}

    except Exception as e:
        logger.error(f"Erreur calcul statistiques: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


@app.post(f"{settings.API_PREFIX}/stats/correlation")
@limiter.limit(settings.RATE_LIMIT)
async def calculate_correlation(
    request: Request,
    file: UploadFile = File(...),
    method: str = Query("pearson", regex="^(pearson|spearman|kendall)$"),
    loader: DataLoaderRepository = Depends(get_data_loader),
    stats_calc: StatisticsCalculator = Depends(get_stats_calc)
):
    """
    Calcule la matrice de corrélation.
    """
    temp_path = None
    try:
        temp_path = settings.UPLOAD_DIR / f"corr_{datetime.now().timestamp()}_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        df = loader.load_data(temp_path)

        # Calcul de la corrélation
        corr_matrix = stats_calc.calculate_correlation_matrix(df, method=method)

        return {
            "success": True,
            "method": method,
            "correlation_matrix": corr_matrix.to_dict()
        }

    except Exception as e:
        logger.error(f"Erreur calcul corrélation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


# ====================
# ROUTES DE GESTION DU CACHE
# ====================

@app.get(f"{settings.API_PREFIX}/cache/stats")
async def cache_statistics():
    """Récupère les statistiques du cache Redis."""
    stats = get_cache_stats()
    return {"success": True, "cache_stats": stats}


@app.delete(f"{settings.API_PREFIX}/cache/clear")
async def clear_cache():
    """Vide complètement le cache (ADMIN)."""
    if cache.is_available:
        cache.clear()
        return {"success": True, "message": "Cache vidé"}
    return {"success": False, "message": "Cache non disponible"}


@app.delete(f"{settings.API_PREFIX}/cache/{key}")
async def delete_cache_key(key: str):
    """Supprime une clé spécifique du cache."""
    if cache.is_available:
        deleted = cache.delete(key)
        return {"success": deleted, "key": key}
    return {"success": False, "message": "Cache non disponible"}


# ====================
# GESTIONNAIRE D'ERREURS
# ====================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Gestionnaire global des exceptions."""
    logger.error(f"Exception globale: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erreur interne du serveur", "error": str(exc)}
    )


# ====================
# ÉVÉNEMENTS DE DÉMARRAGE
# ====================

@app.on_event("startup")
async def startup_event():
    """Actions au démarrage de l'API."""
    logger.info(f"Démarrage de l'API {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environnement: {settings.ENVIRONMENT}")
    logger.info(f"Docs disponibles sur: /api/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Actions à l'arrêt de l'API."""
    logger.info("Arrêt de l'API")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        workers=settings.API_WORKERS if not settings.DEBUG else 1
    )
