"""
Point d'entrée principal de l'application d'analyse de données.
Orchestre tous les modules pour un workflow complet.
"""
import sys
from pathlib import Path
from typing import Optional
import argparse
import pandas as pd

from config import settings
from utils.logger import get_logger, PerformanceLogger
from data_loader.csv_loader import DataLoaderRepository
from data_loader.data_validator import DataValidator, ValidationSchema
from data_processor.cleaner import DataCleaner, ImputationStrategy
from data_processor.aggregator import DataAggregator
from data_processor.statistics import StatisticsCalculator
from visualization.chart_builder import ChartBuilder
from visualization.report_generator import ReportGenerator


logger = get_logger(__name__)


class DataAnalysisPipeline:
    """
    Pipeline complet d'analyse de données.
    
    Workflow:
    1. Chargement des données
    2. Validation
    3. Nettoyage
    4. Analyse et statistiques
    5. Visualisations
    6. Génération de rapport
    7. Export des résultats
    
    Example:
        >>> pipeline = DataAnalysisPipeline()
        >>> pipeline.run("data/vente_2025.csv", output_dir="output/")
    """
    
    def __init__(self):
        """Initialise tous les composants du pipeline."""
        logger.info("=" * 80)
        logger.info("Initialisation du Pipeline d'Analyse de Données")
        logger.info("=" * 80)
        
        self.loader = DataLoaderRepository()
        self.validator = DataValidator(strict_mode=False)
        self.cleaner = DataCleaner()
        self.aggregator = DataAggregator()
        self.stats_calc = StatisticsCalculator()
        self.chart_builder = ChartBuilder()
        self.report_gen = ReportGenerator()
        
        self.df = None
        self.df_clean = None
        
        logger.info("Pipeline initialisé avec succès")
    
    def run(
        self,
        file_path: str,
        output_dir: str = "outputs",
        skip_cleaning: bool = False,
        skip_validation: bool = False,
        generate_report: bool = True,
        export_excel: bool = True
    ) -> bool:
        """
        Execute le pipeline complet d'analyse.
        
        Args:
            file_path: Chemin du fichier de données
            output_dir: Répertoire de sortie
            skip_cleaning: Ignorer l'étape de nettoyage
            skip_validation: Ignorer la validation
            generate_report: Générer le rapport HTML/PDF
            export_excel: Exporter les résultats en Excel
            
        Returns:
            bool: True si succès, False sinon
        """
        with PerformanceLogger(logger, "PIPELINE COMPLET"):
            try:
                logger.info("\n" + "=" * 80)
                logger.info("DÉMARRAGE DU PIPELINE D'ANALYSE")
                logger.info("=" * 80)
                logger.info(f"Fichier source: {file_path}")
                logger.info(f"Répertoire de sortie: {output_dir}")
                
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                # Étape 1: Chargement
                if not self.load_data(file_path):
                    return False
                
                # Étape 2: Validation
                if not skip_validation:
                    if not self.validate_data():
                        logger.warning("Validation échouée, mais continuation du pipeline")
                
                # Étape 3: Nettoyage
                if not skip_cleaning:
                    self.clean_data()
                else:
                    self.df_clean = self.df.copy()
                    logger.info("Nettoyage ignoré (skip_cleaning=True)")
                
                # Étape 4: Analyse et statistiques
                kpis = self.calculate_kpis()
                self.display_kpis(kpis)
                
                # Étape 5: Agrégations
                aggregations = self.perform_aggregations()
                
                # Étape 6: Statistiques avancées
                stats_report = self.generate_statistics()
                
                # Étape 7: Visualisations
                charts_paths = self.generate_visualizations(output_path)
                
                # Étape 8: Rapport HTML/PDF
                if generate_report:
                    report_path = self.generate_report(output_path)
                    logger.info(f"✓ Rapport généré: {report_path}")
                
                # Étape 9: Export Excel
                if export_excel:
                    excel_path = self.export_results_excel(
                        output_path,
                        aggregations,
                        stats_report
                    )
                    logger.info(f"✓ Export Excel: {excel_path}")
                
                logger.info("\n" + "=" * 80)
                logger.info("✓ PIPELINE TERMINÉ AVEC SUCCÈS")
                logger.info("=" * 80)
                
                return True
            
            except Exception as e:
                logger.error(f"✗ ÉCHEC DU PIPELINE: {str(e)}", exc_info=True)
                return False
    
    def load_data(self, file_path: str) -> bool:
        """
        Charge les données depuis un fichier.
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            bool: True si succès
        """
        logger.info("\n[ÉTAPE 1/9] Chargement des données")
        logger.info("-" * 80)
        
        try:
            self.df = self.loader.load_data(file_path)
            
            logger.info(f"✓ Données chargées: {len(self.df)} lignes, {len(self.df.columns)} colonnes")
            logger.info(f"  Colonnes: {list(self.df.columns)}")
            logger.info(f"  Mémoire utilisée: {self.df.memory_usage(deep=True).sum() / (1024**2):.2f} MB")
            
            return True
        except Exception as e:
            logger.error(f"✗ Échec du chargement: {str(e)}")
            return False
    
    def validate_data(self) -> bool:
        """
        Valide la qualité des données.
        
        Returns:
            bool: True si validation réussie
        """
        logger.info("\n[ÉTAPE 2/9] Validation des données")
        logger.info("-" * 80)
        
        # Utiliser le schéma de validation pour les ventes
        result = self.validator.validate_sales_data(self.df)
        
        logger.info(f"Résultat de validation: {'✓ VALIDE' if result.is_valid else '✗ INVALIDE'}")
        
        if result.errors:
            logger.error(f"Erreurs ({len(result.errors)}):")
            for error in result.errors:
                logger.error(f"  - {error}")
        
        if result.warnings:
            logger.warning(f"Avertissements ({len(result.warnings)}):")
            for warning in result.warnings:
                logger.warning(f"  - {warning}")
        
        # Afficher les métriques de qualité
        logger.info("Métriques de qualité:")
        for key, value in result.metrics.items():
            if key != 'column_types':
                logger.info(f"  {key}: {value}")
        
        return result.is_valid
    
    def clean_data(self):
        """Nettoie les données."""
        logger.info("\n[ÉTAPE 3/9] Nettoyage des données")
        logger.info("-" * 80)
        
        # Conversion de la date
        if 'date' in self.df.columns:
            self.df = self.cleaner.convert_dates(self.df, ['date'])
        
        # Nettoyage complet
        self.df_clean = self.cleaner.clean(
            self.df,
            remove_outliers=False,  # Configurable
            impute_missing=True,
            normalize=False,
            encode_categorical=False,
            clean_strings=True
        )
        
        logger.info(f"✓ Nettoyage terminé")
        logger.info(f"  Lignes avant: {len(self.df)}, après: {len(self.df_clean)}")
    
    def calculate_kpis(self) -> dict:
        """
        Calcule les KPIs métier.
        
        Returns:
            dict: KPIs calculés
        """
        logger.info("\n[ÉTAPE 4/9] Calcul des KPIs")
        logger.info("-" * 80)
        
        kpis = self.aggregator.calculate_kpis(self.df_clean)
        
        logger.info("✓ KPIs calculés")
        return kpis
    
    def display_kpis(self, kpis: dict):
        """Affiche les KPIs de manière formatée."""
        logger.info("\n📊 INDICATEURS CLÉS DE PERFORMANCE (KPIs)")
        logger.info("-" * 80)
        logger.info(f"💰 Chiffre d'Affaires Total:  {kpis.get('revenue_total', 0):>15,.2f} €")
        logger.info(f"📦 Transactions:              {kpis.get('transaction_count', 0):>15,}")
        logger.info(f"🛒 Panier Moyen:              {kpis.get('average_basket', 0):>15,.2f} €")
        logger.info(f"📊 Quantité Totale:           {kpis.get('total_quantity', 0):>15,}")
        logger.info(f"💵 Prix Moyen:                {kpis.get('average_price', 0):>15,.2f} €")
        logger.info(f"🏷️  Produits Uniques:          {kpis.get('unique_products', 0):>15,}")
        logger.info(f"📁 Catégories:                {kpis.get('unique_categories', 0):>15,}")
        logger.info(f"🗺️  Villes:                    {kpis.get('unique_cities', 0):>15,}")
        logger.info("-" * 80)
    
    def perform_aggregations(self) -> dict:
        """
        Effectue les agrégations principales.
        
        Returns:
            dict: Résultats des agrégations
        """
        logger.info("\n[ÉTAPE 5/9] Agrégations des données")
        logger.info("-" * 80)
        
        results = {}
        
        # Ventes par catégorie
        results['by_category'] = self.aggregator.calculate_sales_by_category(self.df_clean)
        logger.info(f"✓ Ventes par catégorie: {len(results['by_category'])} catégories")
        
        # Ventes par ville
        results['by_city'] = self.aggregator.calculate_sales_by_city(self.df_clean)
        logger.info(f"✓ Ventes par ville: {len(results['by_city'])} villes")
        
        # Ventes par source
        if 'source' in self.df_clean.columns:
            results['by_source'] = self.aggregator.calculate_sales_by_source(self.df_clean)
            logger.info(f"✓ Ventes par source: {len(results['by_source'])} sources")
        
        # Top produits
        results['top_products'] = self.aggregator.calculate_top_products(self.df_clean, top_n=10)
        logger.info(f"✓ Top 10 produits identifiés")
        
        # Analyse temporelle
        if 'date' in self.df_clean.columns:
            results['trend'] = self.aggregator.calculate_trend_analysis(
                self.df_clean,
                'date',
                period='M'
            )
            logger.info(f"✓ Analyse de tendance mensuelle: {len(results['trend'])} périodes")
        
        return results
    
    def generate_statistics(self) -> dict:
        """
        Génère les statistiques avancées.
        
        Returns:
            dict: Rapport statistique
        """
        logger.info("\n[ÉTAPE 6/9] Calcul des statistiques")
        logger.info("-" * 80)
        
        stats_report = self.stats_calc.generate_statistics_report(self.df_clean)
        
        logger.info("✓ Statistiques générées:")
        logger.info(f"  - {len(stats_report['descriptive_stats'])} variables analysées")
        logger.info(f"  - {len(stats_report['missing_values'])} variables avec valeurs manquantes")
        logger.info(f"  - {len(stats_report['outliers'])} variables avec outliers")
        
        return stats_report
    
    def generate_visualizations(self, output_path: Path) -> dict:
        """
        Génère les visualisations principales.
        
        Args:
            output_path: Répertoire de sortie
            
        Returns:
            dict: Chemins des graphiques générés
        """
        logger.info("\n[ÉTAPE 7/9] Génération des visualisations")
        logger.info("-" * 80)
        
        charts_dir = output_path / "charts"
        charts_dir.mkdir(exist_ok=True)
        
        paths = {}
        
        # 1. Ventes par catégorie
        cat_sales = self.aggregator.calculate_sales_by_category(self.df_clean)
        fig1 = self.chart_builder.create_bar_chart(
            cat_sales,
            x='categorie',
            y='ca_total',
            title='Chiffre d\'Affaires par Catégorie'
        )
        path1 = charts_dir / "ventes_categorie.html"
        self.chart_builder.save_chart(fig1, path1)
        paths['by_category'] = path1
        logger.info(f"✓ Graphique 1/5: {path1.name}")
        
        # 2. Répartition par ville (pie chart)
        city_sales = self.aggregator.calculate_sales_by_city(self.df_clean)
        fig2 = self.chart_builder.create_pie_chart(
            city_sales.head(10),
            names='ville',
            values='ca_total',
            title='Répartition du CA par Ville (Top 10)',
            hole=0.3
        )
        path2 = charts_dir / "repartition_villes.html"
        self.chart_builder.save_chart(fig2, path2)
        paths['by_city'] = path2
        logger.info(f"✓ Graphique 2/5: {path2.name}")
        
        # 3. Évolution temporelle
        if 'date' in self.df_clean.columns:
            trend = self.aggregator.calculate_trend_analysis(self.df_clean, 'date', period='M')
            fig3 = self.chart_builder.create_line_chart(
                trend,
                x='date',
                y='ca_total',
                title='Évolution Mensuelle du Chiffre d\'Affaires'
            )
            path3 = charts_dir / "evolution_ca.html"
            self.chart_builder.save_chart(fig3, path3)
            paths['trend'] = path3
            logger.info(f"✓ Graphique 3/5: {path3.name}")
        
        # 4. Top produits
        top_products = self.aggregator.calculate_top_products(self.df_clean, top_n=10)
        fig4 = self.chart_builder.create_bar_chart(
            top_products,
            x='produit',
            y='ca_total',
            title='Top 10 Produits par CA',
            orientation='h'
        )
        path4 = charts_dir / "top_produits.html"
        self.chart_builder.save_chart(fig4, path4)
        paths['top_products'] = path4
        logger.info(f"✓ Graphique 4/5: {path4.name}")
        
        # 5. Matrice de corrélation (si applicable)
        numeric_cols = self.df_clean.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 1:
            corr_matrix = self.stats_calc.calculate_correlation_matrix(self.df_clean)
            fig5 = self.chart_builder.create_heatmap(
                corr_matrix,
                title='Matrice de Corrélation'
            )
            path5 = charts_dir / "correlation_matrix.html"
            self.chart_builder.save_chart(fig5, path5)
            paths['correlation'] = path5
            logger.info(f"✓ Graphique 5/5: {path5.name}")
        
        logger.info(f"✓ {len(paths)} graphiques générés dans {charts_dir}")
        return paths
    
    def generate_report(self, output_path: Path) -> Path:
        """
        Génère le rapport complet.
        
        Args:
            output_path: Répertoire de sortie
            
        Returns:
            Path: Chemin du rapport
        """
        logger.info("\n[ÉTAPE 8/9] Génération du rapport")
        logger.info("-" * 80)
        
        report_path = output_path / "rapport_analyse.html"
        
        result = self.report_gen.generate_sales_report(
            self.df_clean,
            output_path=str(report_path),
            format='html',
            include_charts=True
        )
        
        logger.info(f"✓ Rapport HTML généré: {result}")
        
        return result
    
    def export_results_excel(
        self,
        output_path: Path,
        aggregations: dict,
        stats_report: dict
    ) -> Path:
        """
        Exporte tous les résultats en Excel.
        
        Args:
            output_path: Répertoire de sortie
            aggregations: Résultats des agrégations
            stats_report: Rapport statistique
            
        Returns:
            Path: Chemin du fichier Excel
        """
        logger.info("\n[ÉTAPE 9/9] Export Excel")
        logger.info("-" * 80)
        
        excel_path = output_path / "resultats_analyse.xlsx"
        
        sheets = {
            'Données Nettoyées': self.df_clean.head(1000),  # Limiter à 1000 lignes
            'Ventes par Catégorie': aggregations['by_category'],
            'Ventes par Ville': aggregations['by_city'],
            'Top Produits': aggregations['top_products']
        }
        
        if 'trend' in aggregations:
            sheets['Évolution Temporelle'] = aggregations['trend']
        
        result = self.report_gen.export_to_excel(
            self.df_clean.head(1000),
            output_path=str(excel_path),
            sheets=sheets
        )
        
        logger.info(f"✓ Export Excel: {result}")
        
        return result


def main():
    """Fonction principale avec arguments en ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Pipeline d'analyse de données de ventes"
    )
    parser.add_argument(
        'file',
        help="Chemin du fichier CSV à analyser"
    )
    parser.add_argument(
        '-o', '--output',
        default='outputs',
        help="Répertoire de sortie (défaut: outputs)"
    )
    parser.add_argument(
        '--skip-cleaning',
        action='store_true',
        help="Ignorer l'étape de nettoyage"
    )
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help="Ignorer la validation"
    )
    parser.add_argument(
        '--no-report',
        action='store_true',
        help="Ne pas générer le rapport"
    )
    parser.add_argument(
        '--no-excel',
        action='store_true',
        help="Ne pas exporter en Excel"
    )
    
    args = parser.parse_args()
    
    # Vérifier que le fichier existe
    if not Path(args.file).exists():
        logger.error(f"Fichier introuvable: {args.file}")
        sys.exit(1)
    
    # Exécuter le pipeline
    pipeline = DataAnalysisPipeline()
    success = pipeline.run(
        file_path=args.file,
        output_dir=args.output,
        skip_cleaning=args.skip_cleaning,
        skip_validation=args.skip_validation,
        generate_report=not args.no_report,
        export_excel=not args.no_excel
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
