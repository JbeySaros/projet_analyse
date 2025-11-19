"""
Module d'agrégation avancée des données.
Calculs de KPIs, groupby multi-niveaux, pivots et time-series.
"""
from typing import List, Dict, Optional, Union, Callable
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from config import settings
from utils.logger import get_logger, PerformanceLogger


logger = get_logger(__name__)


class DataAggregator:
    """
    Classe pour effectuer des agrégations complexes sur les données.
    
    Features:
    - Groupby multi-niveaux
    - Pivots et cross-tabulations
    - Time-series resampling
    - Calcul de KPIs métier
    - Agrégations personnalisées
    
    Example:
        >>> aggregator = DataAggregator()
        >>> result = aggregator.group_by(df, ['categorie', 'ville'], {'prix': 'sum'})
    """
    
    def __init__(self):
        """Initialise l'aggregator."""
        logger.info("DataAggregator initialisé")
    
    def group_by(
        self,
        df: pd.DataFrame,
        group_columns: Union[str, List[str]],
        agg_dict: Dict[str, Union[str, List[str], Callable]],
        sort_by: Optional[str] = None,
        ascending: bool = False
    ) -> pd.DataFrame:
        """
        Effectue un groupby avec agrégations multiples.
        
        Args:
            df: DataFrame source
            group_columns: Colonne(s) de regroupement
            agg_dict: Dictionnaire {colonne: fonction(s)} d'agrégation
            sort_by: Colonne pour trier (optionnel)
            ascending: Ordre de tri
            
        Returns:
            pd.DataFrame: Résultat agrégé
            
        Example:
            >>> result = aggregator.group_by(
            ...     df,
            ...     ['categorie', 'ville'],
            ...     {'prix': ['sum', 'mean'], 'quantite': 'sum'}
            ... )
        """
        with PerformanceLogger(logger, f"group_by({group_columns})"):
            logger.info(f"Groupby sur {group_columns} avec {len(agg_dict)} agrégations")
            
            # Effectuer le groupby
            result = df.groupby(group_columns).agg(agg_dict)
            
            # Aplatir les colonnes multi-niveaux si nécessaire
            if isinstance(result.columns, pd.MultiIndex):
                result.columns = ['_'.join(col).strip() for col in result.columns.values]
            
            # Reset index pour avoir des colonnes normales
            result = result.reset_index()
            
            # Tri optionnel
            if sort_by and sort_by in result.columns:
                result = result.sort_values(sort_by, ascending=ascending)
                logger.debug(f"Résultat trié par '{sort_by}'")
            
            logger.info(f"Groupby terminé: {len(result)} groupes, {len(result.columns)} colonnes")
            return result
    
    def pivot_table(
        self,
        df: pd.DataFrame,
        index: Union[str, List[str]],
        columns: Union[str, List[str]],
        values: str,
        aggfunc: Union[str, Callable] = 'sum',
        fill_value: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Crée un tableau croisé dynamique (pivot table).
        
        Args:
            df: DataFrame source
            index: Colonne(s) pour les lignes
            columns: Colonne(s) pour les colonnes
            values: Colonne à agréger
            aggfunc: Fonction d'agrégation
            fill_value: Valeur pour remplacer les NaN
            
        Returns:
            pd.DataFrame: Pivot table
            
        Example:
            >>> pivot = aggregator.pivot_table(
            ...     df,
            ...     index='categorie',
            ...     columns='ville',
            ...     values='prix',
            ...     aggfunc='sum'
            ... )
        """
        with PerformanceLogger(logger, "pivot_table"):
            logger.info(f"Création pivot: index={index}, columns={columns}, values={values}")
            
            pivot = pd.pivot_table(
                df,
                index=index,
                columns=columns,
                values=values,
                aggfunc=aggfunc,
                fill_value=fill_value
            )
            
            logger.info(f"Pivot créé: shape {pivot.shape}")
            return pivot
    
    def cross_tab(
        self,
        df: pd.DataFrame,
        row_column: str,
        col_column: str,
        normalize: bool = False
    ) -> pd.DataFrame:
        """
        Crée une table de contingence (cross-tabulation).
        
        Args:
            df: DataFrame source
            row_column: Colonne pour les lignes
            col_column: Colonne pour les colonnes
            normalize: Si True, calcule les pourcentages
            
        Returns:
            pd.DataFrame: Table de contingence
            
        Example:
            >>> crosstab = aggregator.cross_tab(df, 'categorie', 'source')
        """
        logger.info(f"Cross-tab: {row_column} x {col_column}")
        
        crosstab = pd.crosstab(
            df[row_column],
            df[col_column],
            normalize='all' if normalize else False
        )
        
        if normalize:
            crosstab = crosstab * 100  # Convertir en pourcentages
            logger.debug("Cross-tab normalisé en pourcentages")
        
        return crosstab
    
    def resample_timeseries(
        self,
        df: pd.DataFrame,
        date_column: str,
        freq: str,
        agg_dict: Dict[str, Union[str, Callable]],
        fill_method: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Rééchantillonne une série temporelle.
        
        Args:
            df: DataFrame source avec colonne date
            date_column: Nom de la colonne date
            freq: Fréquence de rééchantillonnage ('D', 'W', 'M', 'Q', 'Y')
            agg_dict: Dictionnaire d'agrégations
            fill_method: Méthode de remplissage ('ffill', 'bfill', None)
            
        Returns:
            pd.DataFrame: Série temporelle rééchantillonnée
            
        Example:
            >>> # Agréger par mois
            >>> monthly = aggregator.resample_timeseries(
            ...     df,
            ...     'date',
            ...     'M',
            ...     {'prix': 'sum', 'quantite': 'sum'}
            ... )
        """
        with PerformanceLogger(logger, f"resample_timeseries(freq={freq})"):
            df_copy = df.copy()
            
            # S'assurer que la colonne date est en datetime
            if not pd.api.types.is_datetime64_any_dtype(df_copy[date_column]):
                df_copy[date_column] = pd.to_datetime(df_copy[date_column])
                logger.debug(f"Colonne '{date_column}' convertie en datetime")
            
            # Définir l'index sur la date
            df_copy = df_copy.set_index(date_column)
            
            # Rééchantillonner
            resampled = df_copy.resample(freq).agg(agg_dict)
            
            # Remplissage optionnel
            if fill_method:
                resampled = resampled.fillna(method=fill_method)
            
            # Reset index
            resampled = resampled.reset_index()
            
            logger.info(
                f"Rééchantillonnage terminé: {len(resampled)} périodes "
                f"({freq})"
            )
            
            return resampled
    
    def calculate_kpis(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcule des KPIs métier pour les données de ventes.
        
        Args:
            df: DataFrame de ventes
            
        Returns:
            Dict: KPIs calculés
            
        Example:
            >>> kpis = aggregator.calculate_kpis(df)
            >>> print(f"Chiffre d'affaires: {kpis['revenue']:.2f}€")
        """
        logger.info("Calcul des KPIs métier")
        
        # Calcul du chiffre d'affaires
        if 'prix' in df.columns and 'quantite' in df.columns:
            df['revenue'] = df['prix'] * df['quantite']
        
        kpis = {
            # Chiffre d'affaires total
            'revenue_total': float(df['revenue'].sum()) if 'revenue' in df.columns else 0.0,
            
            # Nombre de transactions
            'transaction_count': int(len(df)),
            
            # Panier moyen
            'average_basket': float(df['revenue'].mean()) if 'revenue' in df.columns else 0.0,
            
            # Quantité totale vendue
            'total_quantity': int(df['quantite'].sum()) if 'quantite' in df.columns else 0,
            
            # Prix moyen
            'average_price': float(df['prix'].mean()) if 'prix' in df.columns else 0.0,
            
            # Nombre de produits uniques
            'unique_products': int(df['produit'].nunique()) if 'produit' in df.columns else 0,
            
            # Nombre de catégories
            'unique_categories': int(df['categorie'].nunique()) if 'categorie' in df.columns else 0,
            
            # Nombre de villes
            'unique_cities': int(df['ville'].nunique()) if 'ville' in df.columns else 0,
        }
        
        logger.info(f"KPIs calculés: {len(kpis)} métriques")
        for key, value in kpis.items():
            logger.debug(f"  {key}: {value}")
        
        return kpis
    
    def calculate_sales_by_category(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule les ventes par catégorie.
        
        Args:
            df: DataFrame de ventes
            
        Returns:
            pd.DataFrame: Ventes agrégées par catégorie
        """
        logger.info("Calcul des ventes par catégorie")
        
        if 'revenue' not in df.columns:
            df['revenue'] = df['prix'] * df['quantite']
        
        result = self.group_by(
            df,
            'categorie',
            {
                'revenue': 'sum',
                'quantite': 'sum',
                'prix': 'mean',
                'produit': 'count'
            },
            sort_by='revenue_sum',
            ascending=False
        )
        
        # Renommer pour plus de clarté
        result.columns = ['categorie', 'ca_total', 'quantite_totale', 'prix_moyen', 'nb_transactions']
        
        # Ajouter le pourcentage du CA
        result['ca_percentage'] = (result['ca_total'] / result['ca_total'].sum() * 100).round(2)
        
        logger.info(f"Ventes par catégorie calculées: {len(result)} catégories")
        return result
    
    def calculate_sales_by_city(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule les ventes par ville.
        
        Args:
            df: DataFrame de ventes
            
        Returns:
            pd.DataFrame: Ventes agrégées par ville
        """
        logger.info("Calcul des ventes par ville")
        
        if 'revenue' not in df.columns:
            df['revenue'] = df['prix'] * df['quantite']
        
        result = self.group_by(
            df,
            'ville',
            {
                'revenue': 'sum',
                'quantite': 'sum',
                'produit': 'nunique'
            },
            sort_by='revenue_sum',
            ascending=False
        )
        
        result.columns = ['ville', 'ca_total', 'quantite_totale', 'nb_produits_uniques']
        result['ca_percentage'] = (result['ca_total'] / result['ca_total'].sum() * 100).round(2)
        
        logger.info(f"Ventes par ville calculées: {len(result)} villes")
        return result
    
    def calculate_sales_by_source(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule les ventes par source (web, magasin, etc.).
        
        Args:
            df: DataFrame de ventes
            
        Returns:
            pd.DataFrame: Ventes agrégées par source
        """
        logger.info("Calcul des ventes par source")
        
        if 'revenue' not in df.columns:
            df['revenue'] = df['prix'] * df['quantite']
        
        result = self.group_by(
            df,
            'source',
            {
                'revenue': 'sum',
                'quantite': 'sum',
                'produit': 'count'
            },
            sort_by='revenue_sum',
            ascending=False
        )
        
        result.columns = ['source', 'ca_total', 'quantite_totale', 'nb_transactions']
        result['ca_percentage'] = (result['ca_total'] / result['ca_total'].sum() * 100).round(2)
        
        logger.info(f"Ventes par source calculées: {len(result)} sources")
        return result
    
    def calculate_top_products(
        self,
        df: pd.DataFrame,
        top_n: int = 10,
        metric: str = 'revenue'
    ) -> pd.DataFrame:
        """
        Identifie les produits les plus performants.
        
        Args:
            df: DataFrame de ventes
            top_n: Nombre de produits à retourner
            metric: Métrique pour le classement ('revenue', 'quantite')
            
        Returns:
            pd.DataFrame: Top N produits
            
        Example:
            >>> top = aggregator.calculate_top_products(df, top_n=5)
        """
        logger.info(f"Calcul du Top {top_n} produits (métrique: {metric})")
        
        if 'revenue' not in df.columns:
            df['revenue'] = df['prix'] * df['quantite']
        
        result = self.group_by(
            df,
            'produit',
            {
                'revenue': 'sum',
                'quantite': 'sum',
                'prix': 'mean'
            }
        )
        
        result.columns = ['produit', 'ca_total', 'quantite_totale', 'prix_moyen']
        
        # Trier selon la métrique choisie
        sort_column = 'ca_total' if metric == 'revenue' else 'quantite_totale'
        result = result.sort_values(sort_column, ascending=False).head(top_n)
        
        logger.info(f"Top {len(result)} produits identifiés")
        return result
    
    def calculate_trend_analysis(
        self,
        df: pd.DataFrame,
        date_column: str,
        period: str = 'M'
    ) -> pd.DataFrame:
        """
        Analyse l'évolution des ventes dans le temps.
        
        Args:
            df: DataFrame de ventes
            date_column: Colonne contenant les dates
            period: Période d'agrégation ('D', 'W', 'M', 'Q')
            
        Returns:
            pd.DataFrame: Évolution temporelle des ventes
            
        Example:
            >>> trend = aggregator.calculate_trend_analysis(df, 'date', period='M')
        """
        logger.info(f"Analyse de tendance (période: {period})")
        
        if 'revenue' not in df.columns:
            df['revenue'] = df['prix'] * df['quantite']
        
        trend = self.resample_timeseries(
            df,
            date_column,
            period,
            {
                'revenue': 'sum',
                'quantite': 'sum',
                'produit': 'count'
            }
        )
        
        trend.columns = [date_column, 'ca_total', 'quantite_totale', 'nb_transactions']
        
        # Calculer les variations
        trend['ca_variation_pct'] = trend['ca_total'].pct_change() * 100
        trend['quantite_variation_pct'] = trend['quantite_totale'].pct_change() * 100
        
        # Calculer les moyennes mobiles (3 périodes)
        trend['ca_ma3'] = trend['ca_total'].rolling(window=3).mean()
        
        logger.info(f"Analyse de tendance calculée: {len(trend)} périodes")
        return trend
    
    def calculate_cohort_analysis(
        self,
        df: pd.DataFrame,
        date_column: str,
        customer_column: str
    ) -> pd.DataFrame:
        """
        Effectue une analyse de cohorte (si données clients disponibles).
        
        Args:
            df: DataFrame de ventes
            date_column: Colonne date
            customer_column: Colonne identifiant client
            
        Returns:
            pd.DataFrame: Analyse de cohorte
        """
        logger.info("Analyse de cohorte")
        
        df_copy = df.copy()
        
        # Convertir la date
        if not pd.api.types.is_datetime64_any_dtype(df_copy[date_column]):
            df_copy[date_column] = pd.to_datetime(df_copy[date_column])
        
        # Identifier la première date d'achat pour chaque client
        df_copy['cohort'] = df_copy.groupby(customer_column)[date_column].transform('min')
        df_copy['cohort'] = df_copy['cohort'].dt.to_period('M')
        
        # Période d'achat
        df_copy['period'] = df_copy[date_column].dt.to_period('M')
        
        # Calculer l'âge de la cohorte
        df_copy['cohort_age'] = (
            df_copy['period'].astype('int') - df_copy['cohort'].astype('int')
        )
        
        # Agréger par cohorte et âge
        cohort_data = df_copy.groupby(['cohort', 'cohort_age']).agg({
            customer_column: 'nunique',
            'revenue': 'sum' if 'revenue' in df_copy.columns else 'count'
        }).reset_index()
        
        logger.info(f"Analyse de cohorte calculée: {cohort_data['cohort'].nunique()} cohortes")
        return cohort_data
