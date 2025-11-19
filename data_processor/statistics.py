"""
Module de calcul de statistiques descriptives et inférentielles.
Analyse statistique complète des données.
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from scipy import stats
from config import settings
from utils.logger import get_logger, PerformanceLogger


logger = get_logger(__name__)


@dataclass
class StatisticalSummary:
    """
    Résumé statistique pour une variable numérique.
    
    Attributes:
        column: Nom de la colonne
        count: Nombre de valeurs
        mean: Moyenne
        std: Écart-type
        min: Minimum
        q25: 1er quartile
        median: Médiane
        q75: 3e quartile
        max: Maximum
        skewness: Asymétrie
        kurtosis: Aplatissement
    """
    column: str
    count: int
    mean: float
    std: float
    min: float
    q25: float
    median: float
    q75: float
    max: float
    skewness: float
    kurtosis: float
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire."""
        return {
            'column': self.column,
            'count': self.count,
            'mean': round(self.mean, 2),
            'std': round(self.std, 2),
            'min': round(self.min, 2),
            'q25': round(self.q25, 2),
            'median': round(self.median, 2),
            'q75': round(self.q75, 2),
            'max': round(self.max, 2),
            'skewness': round(self.skewness, 2),
            'kurtosis': round(self.kurtosis, 2)
        }


class StatisticsCalculator:
    """
    Classe pour calculer des statistiques descriptives et inférentielles.
    
    Features:
    - Statistiques descriptives complètes
    - Tests d'hypothèses (t-test, chi2)
    - Corrélations et covariances
    - Distribution et normalité
    - Intervalles de confiance
    
    Example:
        >>> calc = StatisticsCalculator()
        >>> summary = calc.describe_column(df, 'prix')
        >>> print(summary.mean, summary.std)
    """
    
    def __init__(self):
        """Initialise le calculateur."""
        logger.info("StatisticsCalculator initialisé")
    
    def describe_dataframe(self, df: pd.DataFrame) -> Dict[str, StatisticalSummary]:
        """
        Calcule les statistiques descriptives pour toutes les colonnes numériques.
        
        Args:
            df: DataFrame à analyser
            
        Returns:
            Dict: {colonne: StatisticalSummary}
            
        Example:
            >>> stats = calc.describe_dataframe(df)
            >>> print(stats['prix'].mean)
        """
        with PerformanceLogger(logger, "describe_dataframe"):
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            logger.info(f"Calcul des statistiques pour {len(numeric_cols)} colonnes")
            
            results = {}
            for col in numeric_cols:
                results[col] = self.describe_column(df, col)
            
            return results
    
    def describe_column(self, df: pd.DataFrame, column: str) -> StatisticalSummary:
        """
        Calcule les statistiques descriptives pour une colonne.
        
        Args:
            df: DataFrame
            column: Nom de la colonne
            
        Returns:
            StatisticalSummary: Statistiques de la colonne
            
        Example:
            >>> summary = calc.describe_column(df, 'prix')
        """
        data = df[column].dropna()
        
        summary = StatisticalSummary(
            column=column,
            count=int(len(data)),
            mean=float(data.mean()),
            std=float(data.std()),
            min=float(data.min()),
            q25=float(data.quantile(0.25)),
            median=float(data.median()),
            q75=float(data.quantile(0.75)),
            max=float(data.max()),
            skewness=float(data.skew()),
            kurtosis=float(data.kurtosis())
        )
        
        logger.debug(f"Statistiques calculées pour '{column}'")
        return summary
    
    def calculate_correlation_matrix(
        self,
        df: pd.DataFrame,
        method: str = 'pearson',
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Calcule la matrice de corrélation.
        
        Args:
            df: DataFrame
            method: Méthode ('pearson', 'spearman', 'kendall')
            columns: Colonnes à inclure (toutes les numériques si None)
            
        Returns:
            pd.DataFrame: Matrice de corrélation
            
        Example:
            >>> corr = calc.calculate_correlation_matrix(df)
        """
        logger.info(f"Calcul de la matrice de corrélation ({method})")
        
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        corr_matrix = df[columns].corr(method=method)
        
        logger.info(f"Matrice de corrélation calculée: {corr_matrix.shape}")
        return corr_matrix
    
    def find_strong_correlations(
        self,
        df: pd.DataFrame,
        threshold: float = 0.7,
        method: str = 'pearson'
    ) -> List[Tuple[str, str, float]]:
        """
        Identifie les corrélations fortes entre variables.
        
        Args:
            df: DataFrame
            threshold: Seuil de corrélation (valeur absolue)
            method: Méthode de corrélation
            
        Returns:
            List[Tuple]: [(col1, col2, correlation), ...]
            
        Example:
            >>> strong = calc.find_strong_correlations(df, threshold=0.8)
        """
        logger.info(f"Recherche de corrélations fortes (|r| > {threshold})")
        
        corr_matrix = self.calculate_correlation_matrix(df, method=method)
        
        strong_corr = []
        
        # Parcourir la matrice triangulaire supérieure
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]
                
                if abs(corr_value) >= threshold:
                    strong_corr.append((col1, col2, float(corr_value)))
        
        # Trier par corrélation décroissante
        strong_corr.sort(key=lambda x: abs(x[2]), reverse=True)
        
        logger.info(f"{len(strong_corr)} corrélations fortes trouvées")
        for col1, col2, corr in strong_corr:
            logger.debug(f"  {col1} <-> {col2}: {corr:.3f}")
        
        return strong_corr
    
    def test_normality(
        self,
        df: pd.DataFrame,
        column: str,
        method: str = 'shapiro'
    ) -> Tuple[float, float, bool]:
        """
        Test de normalité d'une distribution.
        
        Args:
            df: DataFrame
            column: Colonne à tester
            method: Méthode ('shapiro', 'kstest')
            
        Returns:
            Tuple: (statistic, p_value, is_normal)
            
        Example:
            >>> stat, p, is_normal = calc.test_normality(df, 'prix')
            >>> if is_normal:
            ...     print("Distribution normale")
        """
        logger.info(f"Test de normalité ({method}) pour '{column}'")
        
        data = df[column].dropna()
        
        if method == 'shapiro':
            statistic, p_value = stats.shapiro(data)
        elif method == 'kstest':
            statistic, p_value = stats.kstest(data, 'norm')
        else:
            raise ValueError(f"Méthode inconnue: {method}")
        
        # Hypothèse nulle: la distribution est normale
        # On rejette H0 si p < 0.05
        is_normal = p_value > 0.05
        
        logger.info(
            f"Test de normalité: statistic={statistic:.4f}, "
            f"p-value={p_value:.4f}, normal={is_normal}"
        )
        
        return float(statistic), float(p_value), is_normal
    
    def t_test_independent(
        self,
        df: pd.DataFrame,
        column: str,
        group_column: str,
        group1: str,
        group2: str
    ) -> Tuple[float, float, bool]:
        """
        Test t de Student pour comparer deux groupes indépendants.
        
        Args:
            df: DataFrame
            column: Colonne à comparer
            group_column: Colonne de regroupement
            group1: Valeur du groupe 1
            group2: Valeur du groupe 2
            
        Returns:
            Tuple: (t_statistic, p_value, significant)
            
        Example:
            >>> t, p, sig = calc.t_test_independent(
            ...     df, 'prix', 'source', 'web', 'magasin'
            ... )
        """
        logger.info(f"T-test: {column} entre {group1} et {group2}")
        
        data1 = df[df[group_column] == group1][column].dropna()
        data2 = df[df[group_column] == group2][column].dropna()
        
        t_stat, p_value = stats.ttest_ind(data1, data2)
        
        # Différence significative si p < 0.05
        is_significant = p_value < 0.05
        
        logger.info(
            f"T-test: t={t_stat:.4f}, p={p_value:.4f}, "
            f"significatif={is_significant}"
        )
        
        return float(t_stat), float(p_value), is_significant
    
    def chi2_test(
        self,
        df: pd.DataFrame,
        col1: str,
        col2: str
    ) -> Tuple[float, float, bool]:
        """
        Test du Chi2 pour l'indépendance de deux variables catégorielles.
        
        Args:
            df: DataFrame
            col1: Première variable catégorielle
            col2: Deuxième variable catégorielle
            
        Returns:
            Tuple: (chi2_statistic, p_value, dependent)
            
        Example:
            >>> chi2, p, dep = calc.chi2_test(df, 'categorie', 'source')
        """
        logger.info(f"Test Chi2 d'indépendance: {col1} vs {col2}")
        
        # Créer la table de contingence
        contingency_table = pd.crosstab(df[col1], df[col2])
        
        chi2_stat, p_value, dof, expected = stats.chi2_contingency(contingency_table)
        
        # Variables dépendantes si p < 0.05
        is_dependent = p_value < 0.05
        
        logger.info(
            f"Chi2 test: chi2={chi2_stat:.4f}, p={p_value:.4f}, "
            f"dépendant={is_dependent}"
        )
        
        return float(chi2_stat), float(p_value), is_dependent
    
    def confidence_interval(
        self,
        df: pd.DataFrame,
        column: str,
        confidence: float = 0.95
    ) -> Tuple[float, float, float]:
        """
        Calcule l'intervalle de confiance pour la moyenne.
        
        Args:
            df: DataFrame
            column: Colonne
            confidence: Niveau de confiance (0.95 = 95%)
            
        Returns:
            Tuple: (mean, lower_bound, upper_bound)
            
        Example:
            >>> mean, lower, upper = calc.confidence_interval(df, 'prix', 0.95)
            >>> print(f"95% CI: [{lower:.2f}, {upper:.2f}]")
        """
        data = df[column].dropna()
        
        mean = data.mean()
        std_error = stats.sem(data)
        
        # Intervalle de confiance
        margin = std_error * stats.t.ppf((1 + confidence) / 2, len(data) - 1)
        
        lower = mean - margin
        upper = mean + margin
        
        logger.info(
            f"IC à {confidence*100}% pour '{column}': "
            f"[{lower:.2f}, {upper:.2f}] (moyenne: {mean:.2f})"
        )
        
        return float(mean), float(lower), float(upper)
    
    def calculate_percentiles(
        self,
        df: pd.DataFrame,
        column: str,
        percentiles: List[float] = None
    ) -> Dict[float, float]:
        """
        Calcule les percentiles d'une distribution.
        
        Args:
            df: DataFrame
            column: Colonne
            percentiles: Liste des percentiles (ex: [0.1, 0.25, 0.5, 0.75, 0.9])
            
        Returns:
            Dict: {percentile: valeur}
            
        Example:
            >>> percs = calc.calculate_percentiles(df, 'prix', [0.25, 0.5, 0.75])
        """
        if percentiles is None:
            percentiles = [0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]
        
        data = df[column].dropna()
        
        results = {}
        for p in percentiles:
            results[p] = float(data.quantile(p))
        
        logger.info(f"Percentiles calculés pour '{column}': {len(results)} valeurs")
        
        return results
    
    def outlier_detection(
        self,
        df: pd.DataFrame,
        column: str,
        method: str = 'iqr'
    ) -> Tuple[pd.Series, int]:
        """
        Détecte les outliers dans une colonne.
        
        Args:
            df: DataFrame
            column: Colonne à analyser
            method: Méthode ('iqr' ou 'zscore')
            
        Returns:
            Tuple: (mask_outliers, count)
            
        Example:
            >>> mask, count = calc.outlier_detection(df, 'prix', method='iqr')
            >>> outliers = df[mask]
        """
        logger.info(f"Détection des outliers ({method}) pour '{column}'")
        
        data = df[column]
        
        if method == 'iqr':
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            
            mask = (data < lower) | (data > upper)
        
        elif method == 'zscore':
            z_scores = np.abs((data - data.mean()) / data.std())
            mask = z_scores > 3
        
        else:
            raise ValueError(f"Méthode inconnue: {method}")
        
        count = mask.sum()
        percentage = (count / len(data)) * 100
        
        logger.info(f"{count} outliers détectés ({percentage:.1f}%)")
        
        return mask, int(count)
    
    def generate_statistics_report(self, df: pd.DataFrame) -> Dict:
        """
        Génère un rapport statistique complet.
        
        Args:
            df: DataFrame à analyser
            
        Returns:
            Dict: Rapport complet
            
        Example:
            >>> report = calc.generate_statistics_report(df)
        """
        with PerformanceLogger(logger, "generate_statistics_report"):
            logger.info("Génération du rapport statistique complet")
            
            report = {
                'overview': {
                    'n_rows': len(df),
                    'n_columns': len(df.columns),
                    'n_numeric': len(df.select_dtypes(include=[np.number]).columns),
                    'n_categorical': len(df.select_dtypes(include=['object', 'category']).columns),
                    'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024**2)
                },
                'descriptive_stats': {},
                'missing_values': {},
                'correlations': None,
                'outliers': {}
            }
            
            # Statistiques descriptives
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            for col in numeric_cols:
                summary = self.describe_column(df, col)
                report['descriptive_stats'][col] = summary.to_dict()
            
            # Valeurs manquantes
            for col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    report['missing_values'][col] = {
                        'count': int(missing_count),
                        'percentage': float(missing_count / len(df) * 100)
                    }
            
            # Matrice de corrélation
            if len(numeric_cols) > 1:
                report['correlations'] = self.calculate_correlation_matrix(df).to_dict()
            
            # Outliers
            for col in numeric_cols:
                _, count = self.outlier_detection(df, col)
                if count > 0:
                    report['outliers'][col] = count
            
            logger.info("Rapport statistique généré")
            return report
