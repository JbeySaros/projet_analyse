"""
Module de gestion du cache Redis.
Fournit des décorateurs et fonctions pour la mise en cache.
"""
import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
import redis
from config import settings
from utils.logger import get_logger


logger = get_logger(__name__)


class RedisCache:
    """
    Gestionnaire de cache Redis avec pattern Singleton.
    
    Features:
    - Mise en cache automatique
    - Invalidation par clé ou pattern
    - TTL configurable
    - Sérialisation JSON automatique
    
    Example:
        >>> cache = RedisCache()
        >>> cache.set("key", {"data": "value"}, ttl=3600)
        >>> result = cache.get("key")
    """
    
    _instance: Optional["RedisCache"] = None
    _client: Optional[redis.Redis] = None
    
    def __new__(cls):
        """Pattern Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialise la connexion Redis."""
        if self._initialized:
            return
        
        if not settings.CACHE_ENABLED:
            logger.warning("Cache Redis désactivé dans la configuration")
            self._client = None
            self._initialized = True
            return
        
        try:
            self._client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test de connexion
            self._client.ping()
            logger.info(f"✓ Connexion Redis établie: {settings.REDIS_URL}")
        except Exception as e:
            logger.error(f"✗ Échec connexion Redis: {str(e)}")
            self._client = None
        
        self._initialized = True
    
    @property
    def is_available(self) -> bool:
        """Vérifie si Redis est disponible."""
        if not settings.CACHE_ENABLED or self._client is None:
            return False
        
        try:
            self._client.ping()
            return True
        except:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache.
        
        Args:
            key: Clé du cache
            
        Returns:
            Valeur désérialisée ou None
        """
        if not self.is_available:
            return None
        
        try:
            value = self._client.get(key)
            if value is None:
                logger.debug(f"Cache MISS: {key}")
                return None
            
            logger.debug(f"Cache HIT: {key}")
            return json.loads(value)
        except Exception as e:
            logger.error(f"Erreur lecture cache {key}: {str(e)}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Stocke une valeur dans le cache.
        
        Args:
            key: Clé du cache
            value: Valeur à stocker (sérialisée en JSON)
            ttl: Time-to-live en secondes (défaut: settings.CACHE_TTL)
            
        Returns:
            True si succès, False sinon
        """
        if not self.is_available:
            return False
        
        ttl = ttl or settings.CACHE_TTL
        
        try:
            serialized = json.dumps(value, default=str)
            self._client.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Erreur écriture cache {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Supprime une clé du cache.
        
        Args:
            key: Clé à supprimer
            
        Returns:
            True si supprimé, False sinon
        """
        if not self.is_available:
            return False
        
        try:
            deleted = self._client.delete(key)
            logger.debug(f"Cache DELETE: {key} (deleted: {deleted})")
            return deleted > 0
        except Exception as e:
            logger.error(f"Erreur suppression cache {key}: {str(e)}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Supprime toutes les clés correspondant à un pattern.
        
        Args:
            pattern: Pattern Redis (ex: "user:*")
            
        Returns:
            Nombre de clés supprimées
        """
        if not self.is_available:
            return 0
        
        try:
            keys = self._client.keys(pattern)
            if keys:
                deleted = self._client.delete(*keys)
                logger.info(f"Cache DELETE pattern '{pattern}': {deleted} clés")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Erreur suppression pattern {pattern}: {str(e)}")
            return 0
    
    def clear(self) -> bool:
        """
        Vide complètement le cache (ATTENTION: dangereux).
        
        Returns:
            True si succès
        """
        if not self.is_available:
            return False
        
        try:
            self._client.flushdb()
            logger.warning("Cache complètement vidé (FLUSHDB)")
            return True
        except Exception as e:
            logger.error(f"Erreur vidage cache: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Vérifie si une clé existe."""
        if not self.is_available:
            return False
        
        try:
            return self._client.exists(key) > 0
        except:
            return False
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Récupère le TTL d'une clé (en secondes)."""
        if not self.is_available:
            return None
        
        try:
            ttl = self._client.ttl(key)
            return ttl if ttl >= 0 else None
        except:
            return None
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Incrémente une valeur numérique."""
        if not self.is_available:
            return None
        
        try:
            return self._client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Erreur increment {key}: {str(e)}")
            return None


# Instance globale
cache = RedisCache()


def generate_cache_key(*args, **kwargs) -> str:
    """
    Génère une clé de cache unique basée sur les arguments.
    
    Args:
        *args: Arguments positionnels
        **kwargs: Arguments nommés
        
    Returns:
        Clé de cache hashée
        
    Example:
        >>> key = generate_cache_key("user", user_id=123, action="view")
        >>> # Retourne: "cache:abc123def456..."
    """
    # Créer une représentation des arguments
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    
    # Hasher pour obtenir une clé courte et unique
    key_string = ":".join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"cache:{key_hash}"


def cached(
    ttl: Optional[int] = None,
    key_prefix: str = "",
    key_builder: Optional[Callable] = None
):
    """
    Décorateur pour mettre en cache le résultat d'une fonction.
    
    Args:
        ttl: Time-to-live en secondes
        key_prefix: Préfixe pour la clé de cache
        key_builder: Fonction personnalisée pour générer la clé
        
    Example:
        >>> @cached(ttl=3600, key_prefix="stats")
        ... def calculate_statistics(df):
        ...     # Calcul lourd
        ...     return stats
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Ne pas utiliser le cache si désactivé
            if not cache.is_available:
                return func(*args, **kwargs)
            
            # Générer la clé de cache
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = f"{key_prefix}:{func.__name__}:"
                cache_key += generate_cache_key(*args, **kwargs)
            
            # Vérifier le cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Résultat en cache pour {func.__name__}")
                return cached_result
            
            # Calculer et mettre en cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        # Ajouter une méthode pour invalider le cache
        def invalidate_cache(*args, **kwargs):
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = f"{key_prefix}:{func.__name__}:"
                cache_key += generate_cache_key(*args, **kwargs)
            cache.delete(cache_key)
        
        wrapper.invalidate_cache = invalidate_cache
        return wrapper
    
    return decorator


def cache_analysis_result(file_hash: str, analysis_type: str):
    """
    Décorateur spécialisé pour mettre en cache les résultats d'analyse.
    
    Args:
        file_hash: Hash du fichier analysé
        analysis_type: Type d'analyse (kpis, stats, aggregations, etc.)
        
    Example:
        >>> @cache_analysis_result(file_hash="abc123", analysis_type="kpis")
        ... def calculate_kpis(df):
        ...     return aggregator.calculate_kpis(df)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"analysis:{file_hash}:{analysis_type}"
            
            # Vérifier le cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"✓ Analyse en cache: {analysis_type}")
                return cached_result
            
            # Calculer
            logger.info(f"⚙ Calcul de l'analyse: {analysis_type}")
            result = func(*args, **kwargs)
            
            # Mettre en cache
            cache.set(cache_key, result, ttl=settings.CACHE_TTL)
            
            return result
        
        return wrapper
    
    return decorator


# Fonctions helper
def invalidate_file_cache(file_hash: str):
    """Invalide tous les caches liés à un fichier."""
    pattern = f"analysis:{file_hash}:*"
    deleted = cache.delete_pattern(pattern)
    logger.info(f"Invalidation cache fichier {file_hash}: {deleted} clés")


def get_cache_stats() -> dict:
    """Récupère des statistiques sur le cache Redis."""
    if not cache.is_available:
        return {"available": False}
    
    try:
        info = cache._client.info()
        return {
            "available": True,
            "used_memory_mb": info.get("used_memory", 0) / (1024**2),
            "keys_count": cache._client.dbsize(),
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": (
                info.get("keyspace_hits", 0) / 
                (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
            ) * 100
        }
    except Exception as e:
        logger.error(f"Erreur récupération stats cache: {str(e)}")
        return {"available": False, "error": str(e)}
