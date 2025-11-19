"""
Module de nettoyage avancé des données.
Gère les outliers, normalisation, imputation et encodage.
"""
from typing import List, Optional, Literal, Dict
from enum import Enum
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.impute import SimpleImputer, KNNImputer
from config import settings
from utils.logger import get_logger, PerformanceLogger


logger = get_logger(__name__)


class ImputationStrategy(Enum):
    """Stratégies d'imputation des valeurs manquantes."""
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "most_frequent"
    CONSTANT = "constant"
    KNN = "knn"
    FORWARD_FILL = "ffill"
    BACKWARD_FILL = "bfill"


class ScalingMethod(Enum):
    """Méthodes de normalisation."""
    STANDARD = "standard"  # Z-score normalization
    MINMAX = "minmax"      # Scale to [0, 1]
    ROBUST = "robust"      # Robust to outliers


class DataCleaner:
    """
    Classe pour le nettoyage avancé des données.
    
    Features:
    - Détection et traitement des outliers (IQR, Z-score)
    - Imputation des valeurs manquantes (mean, median, KNN)
    - Normalisation/Standardisation
    - Encodage des variables catégorielles
    - Nettoyage des chaînes de caractères
    
    Example:
        >>> cleaner = DataCleaner()
        >>> df_clean = cleaner.clean(df, remove_outliers=True, impute_missing=True)
    """
    
    def __init__(self):
        """Initialise le cleaner."""
        self.scalers: Dict[str, any] = {}
        self.encoders: Dict[str, LabelEncoder] = {}
        logger.info("DataCleaner initialisé")
    
    def clean(
        self,
        df: pd.DataFrame,
        remove_outliers: bool = True,
        impute_missing: bool = True,
        normalize: bool = False,
        encode_categorical: bool = False,
        clean_strings: bool = True
    ) -> pd.DataFrame:
        """
        Pipeline de nettoyage complet.
        
        Args:
            df: DataFrame à nettoyer
            remove_outliers: Supprimer les outliers
            impute_missing: Imputer les valeurs manquantes
            normalize: Normaliser les colonnes numériques
            encode_categorical: Encoder les variables catégorielles
            clean_strings: Nettoyer les chaînes de caractères
            
        Returns:
            pd.DataFrame: DataFrame nettoyé (copie)
            
        Example:
            >>> cleaner = DataCleaner()
            >>> df_clean = cleaner.clean(df, remove_outliers=True)
        """
        with PerformanceLogger(logger, "clean_dataframe"):
            df_clean = df.copy()
            
            logger.info(f"Nettoyage démarré - Shape initiale: {df_clean.shape}")
            
            # 1. Nettoyage des chaînes
            if clean_strings:
                df_clean = self.clean_string_columns(df_clean)
            
            # 2. Suppression des outliers
            if remove_outliers:
                df_clean = self.remove_outliers(df_clean)
            
            # 3. Imputation des valeurs manquantes
            if impute_missing:
                df_clean = self.impute_missing_values(df_clean)
            
            # 4. Normalisation
            if normalize:
                df_clean = self.normalize_numeric_columns(df_clean)
            
            # 5. Encodage catégoriel
            if encode_categorical:
                df_clean = self.encode_categorical_columns(df_clean)
            
            logger.info(f"Nettoyage terminé - Shape finale: {df_clean.shape}")
            
            return df_clean
    
    def remove_outliers(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: Literal["iqr", "zscore"] = None
    ) -> pd.DataFrame:
        """
        Supprime les outliers des colonnes numériques.
        
        Args:
            df: DataFrame
            columns: Colonnes à traiter (toutes les numériques si None)
            method: Méthode de détection ("iqr" ou "zscore")
            
        Returns:
            pd.DataFrame: DataFrame sans outliers
            
        Example:
            >>> df_clean = cleaner.remove_outliers(df, method="iqr")
        """
        method = method or settings.OUTLIER_METHOD
        df_clean = df.copy()
        
        if columns is None:
            columns = df_clean.select_dtypes(include=[np.number]).columns.tolist()
        
        initial_rows = len(df_clean)
        
        logger.info(f"Suppression des outliers ({method}) sur {len(columns)} colonnes")
        
        for column in columns:
            if column not in df_clean.columns:
                continue
            
            before = len(df_clean)
            
            if method == "iqr":
                df_clean = self._remove_outliers_iqr(df_clean, column)
            elif method == "zscore":
                df_clean = self._remove_outliers_zscore(df_clean, column)
            
            removed = before - len(df_clean)
            if removed > 0:
                logger.debug(f"  {column}: {removed} outliers supprimés")
        
        total_removed = initial_rows - len(df_clean)
        logger.info(f"Total outliers supprimés: {total_removed} ({total_removed/initial_rows*100:.1f}%)")
        
        return df_clean
    
    def _remove_outliers_iqr(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Supprime les outliers avec la méthode IQR (Interquartile Range)."""
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        
        threshold = settings.OUTLIER_THRESHOLD
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        
        mask = (df[column] >= lower_bound) & (df[column] <= upper_bound)
        return df[mask]
    
    def _remove_outliers_zscore(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Supprime les outliers avec la méthode Z-score."""
        z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
        mask = z_scores < settings.ZSCORE_THRESHOLD
        return df[mask]
    
    def impute_missing_values(
        self,
        df: pd.DataFrame,
        strategy: ImputationStrategy = ImputationStrategy.MEDIAN,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Impute les valeurs manquantes.
        
        Args:
            df: DataFrame
            strategy: Stratégie d'imputation
            columns: Colonnes à traiter (toutes si None)
            
        Returns:
            pd.DataFrame: DataFrame avec valeurs imputées
            
        Example:
            >>> df = cleaner.impute_missing_values(df, strategy=ImputationStrategy.MEAN)
        """
        df_clean = df.copy()
        
        if columns is None:
            columns = df_clean.columns.tolist()
        
        missing_counts = df_clean[columns].isna().sum()
        columns_with_missing = missing_counts[missing_counts > 0].index.tolist()
        
        if not columns_with_missing:
            logger.info("Aucune valeur manquante à imputer")
            return df_clean
        
        logger.info(
            f"Imputation ({strategy.value}) sur {len(columns_with_missing)} colonnes "
            f"avec valeurs manquantes"
        )
        
        # Séparer numériques et catégorielles
        numeric_cols = df_clean[columns_with_missing].select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df_clean[columns_with_missing].select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Imputation numérique
        if numeric_cols:
            if strategy == ImputationStrategy.KNN:
                imputer = KNNImputer(n_neighbors=5)
                df_clean[numeric_cols] = imputer.fit_transform(df_clean[numeric_cols])
                logger.debug(f"  Imputation KNN sur {len(numeric_cols)} colonnes numériques")
            elif strategy in [ImputationStrategy.FORWARD_FILL, ImputationStrategy.BACKWARD_FILL]:
                method = 'ffill' if strategy == ImputationStrategy.FORWARD_FILL else 'bfill'
                df_clean[numeric_cols] = df_clean[numeric_cols].fillna(method=method)
                logger.debug(f"  Imputation {method} sur {len(numeric_cols)} colonnes numériques")
            else:
                imputer = SimpleImputer(strategy=strategy.value)
                df_clean[numeric_cols] = imputer.fit_transform(df_clean[numeric_cols])
                logger.debug(f"  Imputation {strategy.value} sur {len(numeric_cols)} colonnes numériques")
        
        # Imputation catégorielle (mode ou constant)
        if categorical_cols:
            imputer = SimpleImputer(strategy='most_frequent')
            df_clean[categorical_cols] = imputer.fit_transform(df_clean[categorical_cols])
            logger.debug(f"  Imputation mode sur {len(categorical_cols)} colonnes catégorielles")
        
        logger.info("Imputation terminée")
        return df_clean
    
    def normalize_numeric_columns(
        self,
        df: pd.DataFrame,
        method: ScalingMethod = ScalingMethod.STANDARD,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Normalise les colonnes numériques.
        
        Args:
            df: DataFrame
            method: Méthode de normalisation
            columns: Colonnes à normaliser (toutes les numériques si None)
            
        Returns:
            pd.DataFrame: DataFrame avec colonnes normalisées
            
        Example:
            >>> df = cleaner.normalize_numeric_columns(df, method=ScalingMethod.MINMAX)
        """
        df_clean = df.copy()
        
        if columns is None:
            columns = df_clean.select_dtypes(include=[np.number]).columns.tolist()
        
        if not columns:
            logger.warning("Aucune colonne numérique à normaliser")
            return df_clean
        
        logger.info(f"Normalisation ({method.value}) sur {len(columns)} colonnes")
        
        # Choix du scaler
        if method == ScalingMethod.STANDARD:
            scaler = StandardScaler()
        elif method == ScalingMethod.MINMAX:
            scaler = MinMaxScaler()
        else:
            from sklearn.preprocessing import RobustScaler
            scaler = RobustScaler()
        
        # Appliquer la normalisation
        df_clean[columns] = scaler.fit_transform(df_clean[columns])
        
        # Sauvegarder le scaler pour usage futur
        for col in columns:
            self.scalers[col] = scaler
        
        logger.info("Normalisation terminée")
        return df_clean
    
    def encode_categorical_columns(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: Literal["label", "onehot"] = "label"
    ) -> pd.DataFrame:
        """
        Encode les variables catégorielles.
        
        Args:
            df: DataFrame
            columns: Colonnes à encoder (toutes les catégorielles si None)
            method: "label" (LabelEncoder) ou "onehot" (One-Hot Encoding)
            
        Returns:
            pd.DataFrame: DataFrame avec colonnes encodées
            
        Example:
            >>> df = cleaner.encode_categorical_columns(df, method="onehot")
        """
        df_clean = df.copy()
        
        if columns is None:
            columns = df_clean.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if not columns:
            logger.warning("Aucune colonne catégorielle à encoder")
            return df_clean
        
        logger.info(f"Encodage ({method}) sur {len(columns)} colonnes")
        
        if method == "label":
            for col in columns:
                le = LabelEncoder()
                df_clean[col] = le.fit_transform(df_clean[col].astype(str))
                self.encoders[col] = le
                logger.debug(f"  {col}: {len(le.classes_)} catégories")
        
        elif method == "onehot":
            df_clean = pd.get_dummies(df_clean, columns=columns, drop_first=True)
            logger.debug(f"  Nouvelles colonnes créées: {df_clean.shape[1] - df.shape[1]}")
        
        logger.info("Encodage terminé")
        return df_clean
    
    def clean_string_columns(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Nettoie les colonnes de type chaîne de caractères.
        - Supprime les espaces superflus
        - Uniformise la casse
        - Supprime les caractères spéciaux
        
        Args:
            df: DataFrame
            columns: Colonnes à nettoyer (toutes les strings si None)
            
        Returns:
            pd.DataFrame: DataFrame avec chaînes nettoyées
        """
        df_clean = df.copy()
        
        if columns is None:
            columns = df_clean.select_dtypes(include=['object']).columns.tolist()
        
        logger.info(f"Nettoyage des chaînes sur {len(columns)} colonnes")
        
        for col in columns:
            if col not in df_clean.columns:
                continue
            
            # Supprimer les espaces en début/fin
            df_clean[col] = df_clean[col].str.strip()
            
            # Remplacer les espaces multiples par un seul
            df_clean[col] = df_clean[col].str.replace(r'\s+', ' ', regex=True)
        
        logger.debug("Nettoyage des chaînes terminé")
        return df_clean
    
    def convert_dates(
        self,
        df: pd.DataFrame,
        date_columns: List[str],
        format: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Convertit les colonnes en type datetime.
        
        Args:
            df: DataFrame
            date_columns: Colonnes à convertir
            format: Format de date (auto-détecté si None)
            
        Returns:
            pd.DataFrame: DataFrame avec dates converties
            
        Example:
            >>> df = cleaner.convert_dates(df, ['date'], format='%Y-%m-%d')
        """
        df_clean = df.copy()
        
        logger.info(f"Conversion en datetime pour {len(date_columns)} colonnes")
        
        for col in date_columns:
            if col not in df_clean.columns:
                logger.warning(f"Colonne '{col}' introuvable, ignorée")
                continue
            
            try:
                df_clean[col] = pd.to_datetime(df_clean[col], format=format, errors='coerce')
                null_count = df_clean[col].isna().sum()
                logger.debug(f"  {col}: converti ({null_count} valeurs invalides)")
            except Exception as e:
                logger.error(f"  Erreur lors de la conversion de '{col}': {str(e)}")
        
        return df_clean
