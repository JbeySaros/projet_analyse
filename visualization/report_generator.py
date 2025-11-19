"""
Module de génération de rapports complets (HTML/PDF).
Agrège données, statistiques et visualisations.
"""
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from config import settings
from utils.logger import get_logger, PerformanceLogger
from visualization.chart_builder import ChartBuilder
from data_processor.statistics import StatisticsCalculator
from data_processor.aggregator import DataAggregator


logger = get_logger(__name__)


class ReportGenerator:
    """
    Classe pour générer des rapports d'analyse complets.
    
    Features:
    - Rapports HTML interactifs
    - Export PDF professionnel
    - Inclusion de graphiques et tableaux
    - Templates personnalisables
    - Statistiques et KPIs
    
    Example:
        >>> generator = ReportGenerator()
        >>> generator.generate_sales_report(
        ...     df,
        ...     output_path='output/rapport_ventes.html'
        ... )
    """
    
    HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        header {
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        h2 {
            color: #34495e;
            font-size: 1.8em;
            margin: 30px 0 15px 0;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }
        h3 {
            color: #555;
            font-size: 1.3em;
            margin: 20px 0 10px 0;
        }
        .metadata {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .kpi-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .kpi-label {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }
        .kpi-value {
            font-size: 2em;
            font-weight: bold;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        th {
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .chart-container {
            margin: 30px 0;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }
        .info {
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 15px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{{ title }}</h1>
            <div class="metadata">
                <p>Généré le {{ date }} | Période: {{ period }}</p>
                <p>Données: {{ data_info }}</p>
            </div>
        </header>
        
        <section>
            <h2>📊 Indicateurs Clés de Performance (KPIs)</h2>
            <div class="kpi-grid">
                {% for kpi in kpis %}
                <div class="kpi-card">
                    <div class="kpi-label">{{ kpi.label }}</div>
                    <div class="kpi-value">{{ kpi.value }}</div>
                </div>
                {% endfor %}
            </div>
        </section>
        
        {{ content | safe }}
        
        <footer class="footer">
            <p>Rapport généré automatiquement par la Plateforme d'Analyse de Données</p>
            <p>{{ company_name }} - {{ year }}</p>
        </footer>
    </div>
</body>
</html>
    """
    
    def __init__(self):
        """Initialise le générateur de rapports."""
        self.chart_builder = ChartBuilder()
        self.stats_calc = StatisticsCalculator()
        self.aggregator = DataAggregator()
        
        logger.info("ReportGenerator initialisé")
    
    def generate_sales_report(
        self,
        df: pd.DataFrame,
        output_path: str,
        format: str = 'html',
        include_charts: bool = True
    ) -> Path:
        """
        Génère un rapport complet d'analyse des ventes.
        
        Args:
            df: DataFrame de ventes
            output_path: Chemin de sortie
            format: Format ('html' ou 'pdf')
            include_charts: Inclure les graphiques
            
        Returns:
            Path: Chemin du fichier généré
            
        Example:
            >>> generator = ReportGenerator()
            >>> path = generator.generate_sales_report(df, 'rapport.html')
        """
        with PerformanceLogger(logger, "generate_sales_report"):
            logger.info(f"Génération du rapport de ventes (format: {format})")
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Préparation des données
            if 'revenue' not in df.columns and 'prix' in df.columns and 'quantite' in df.columns:
                df['revenue'] = df['prix'] * df['quantite']
            
            # Calcul des KPIs
            kpis = self._prepare_kpis(df)
            
            # Génération du contenu
            content_sections = []
            
            # Section 1: Vue d'ensemble
            content_sections.append(self._generate_overview_section(df))
            
            # Section 2: Analyse par catégorie
            content_sections.append(self._generate_category_analysis(df, include_charts))
            
            # Section 3: Analyse géographique
            content_sections.append(self._generate_geographic_analysis(df, include_charts))
            
            # Section 4: Analyse temporelle
            if 'date' in df.columns:
                content_sections.append(self._generate_temporal_analysis(df, include_charts))
            
            # Section 5: Top produits
            content_sections.append(self._generate_top_products_section(df))
            
            # Section 6: Statistiques détaillées
            content_sections.append(self._generate_statistics_section(df))
            
            # Assemblage du rapport
            content = "\n".join(content_sections)
            
            # Génération HTML
            html_content = self._render_template(
                title="Rapport d'Analyse des Ventes",
                date=datetime.now().strftime("%d/%m/%Y %H:%M"),
                period=self._get_period_info(df),
                data_info=f"{len(df)} transactions, {df['produit'].nunique() if 'produit' in df.columns else 0} produits",
                kpis=kpis,
                content=content,
                company_name="Data Analysis Platform",
                year=datetime.now().year
            )
            
            # Sauvegarde
            if format == 'html':
                output_path = output_path.with_suffix('.html')
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            elif format == 'pdf':
                output_path = output_path.with_suffix('.pdf')
                HTML(string=html_content).write_pdf(output_path)
            
            logger.info(f"Rapport généré: {output_path}")
            return output_path
    
    def _prepare_kpis(self, df: pd.DataFrame) -> List[Dict]:
        """Prépare les KPIs pour l'affichage."""
        kpis_data = self.aggregator.calculate_kpis(df)
        
        kpis = [
            {
                'label': 'Chiffre d\'Affaires Total',
                'value': f"{kpis_data.get('revenue_total', 0):,.2f} €"
            },
            {
                'label': 'Nombre de Transactions',
                'value': f"{kpis_data.get('transaction_count', 0):,}"
            },
            {
                'label': 'Panier Moyen',
                'value': f"{kpis_data.get('average_basket', 0):.2f} €"
            },
            {
                'label': 'Quantité Totale',
                'value': f"{kpis_data.get('total_quantity', 0):,}"
            }
        ]
        
        return kpis
    
    def _generate_overview_section(self, df: pd.DataFrame) -> str:
        """Génère la section vue d'ensemble."""
        html = "<section>\n<h2>📈 Vue d'Ensemble</h2>\n"
        
        # Informations générales
        info = f"""
        <div class="info">
            <h3>Informations Générales</h3>
            <ul>
                <li><strong>Nombre de transactions:</strong> {len(df):,}</li>
                <li><strong>Produits uniques:</strong> {df['produit'].nunique() if 'produit' in df.columns else 'N/A'}</li>
                <li><strong>Catégories:</strong> {df['categorie'].nunique() if 'categorie' in df.columns else 'N/A'}</li>
                <li><strong>Villes:</strong> {df['ville'].nunique() if 'ville' in df.columns else 'N/A'}</li>
            </ul>
        </div>
        """
        html += info
        html += "</section>\n"
        
        return html
    
    def _generate_category_analysis(self, df: pd.DataFrame, include_charts: bool) -> str:
        """Génère l'analyse par catégorie."""
        html = "<section>\n<h2>🏷️ Analyse par Catégorie</h2>\n"
        
        if 'categorie' not in df.columns:
            html += "<p>Données de catégorie non disponibles.</p></section>\n"
            return html
        
        # Agrégation par catégorie
        cat_sales = self.aggregator.calculate_sales_by_category(df)
        
        # Tableau
        html += "<h3>Ventes par Catégorie</h3>\n"
        html += cat_sales.to_html(index=False, classes='table', float_format='%.2f')
        
        # Graphique
        if include_charts:
            fig = self.chart_builder.create_bar_chart(
                cat_sales,
                x='categorie',
                y='ca_total',
                title='Chiffre d\'Affaires par Catégorie'
            )
            chart_html = fig.to_html(include_plotlyjs='cdn', div_id='cat_chart')
            html += f'<div class="chart-container">{chart_html}</div>\n'
        
        html += "</section>\n"
        return html
    
    def _generate_geographic_analysis(self, df: pd.DataFrame, include_charts: bool) -> str:
        """Génère l'analyse géographique."""
        html = "<section>\n<h2>🗺️ Analyse Géographique</h2>\n"
        
        if 'ville' not in df.columns:
            html += "<p>Données géographiques non disponibles.</p></section>\n"
            return html
        
        # Agrégation par ville
        city_sales = self.aggregator.calculate_sales_by_city(df)
        
        # Tableau
        html += "<h3>Ventes par Ville</h3>\n"
        html += city_sales.to_html(index=False, classes='table', float_format='%.2f')
        
        # Graphique
        if include_charts:
            fig = self.chart_builder.create_pie_chart(
                city_sales.head(10),
                names='ville',
                values='ca_total',
                title='Répartition du CA par Ville (Top 10)',
                hole=0.3
            )
            chart_html = fig.to_html(include_plotlyjs='cdn', div_id='city_chart')
            html += f'<div class="chart-container">{chart_html}</div>\n'
        
        html += "</section>\n"
        return html
    
    def _generate_temporal_analysis(self, df: pd.DataFrame, include_charts: bool) -> str:
        """Génère l'analyse temporelle."""
        html = "<section>\n<h2>📅 Analyse Temporelle</h2>\n"
        
        # Conversion de la date si nécessaire
        df_copy = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_copy['date']):
            df_copy['date'] = pd.to_datetime(df_copy['date'])
        
        # Tendance mensuelle
        trend = self.aggregator.calculate_trend_analysis(df_copy, 'date', period='M')
        
        html += "<h3>Évolution Mensuelle</h3>\n"
        html += trend.to_html(index=False, classes='table', float_format='%.2f')
        
        # Graphique de tendance
        if include_charts:
            fig = self.chart_builder.create_line_chart(
                trend,
                x='date',
                y='ca_total',
                title='Évolution du Chiffre d\'Affaires'
            )
            chart_html = fig.to_html(include_plotlyjs='cdn', div_id='trend_chart')
            html += f'<div class="chart-container">{chart_html}</div>\n'
        
        html += "</section>\n"
        return html
    
    def _generate_top_products_section(self, df: pd.DataFrame) -> str:
        """Génère la section des top produits."""
        html = "<section>\n<h2>⭐ Top Produits</h2>\n"
        
        if 'produit' not in df.columns:
            html += "<p>Données produits non disponibles.</p></section>\n"
            return html
        
        top_products = self.aggregator.calculate_top_products(df, top_n=10)
        
        html += "<h3>Top 10 Produits par CA</h3>\n"
        html += top_products.to_html(index=False, classes='table', float_format='%.2f')
        
        html += "</section>\n"
        return html
    
    def _generate_statistics_section(self, df: pd.DataFrame) -> str:
        """Génère la section statistiques détaillées."""
        html = "<section>\n<h2>📊 Statistiques Détaillées</h2>\n"
        
        # Statistiques descriptives
        stats_dict = self.stats_calc.describe_dataframe(df)
        
        if stats_dict:
            html += "<h3>Statistiques Descriptives</h3>\n"
            stats_df = pd.DataFrame([s.to_dict() for s in stats_dict.values()])
            html += stats_df.to_html(index=False, classes='table', float_format='%.2f')
        
        html += "</section>\n"
        return html
    
    def _get_period_info(self, df: pd.DataFrame) -> str:
        """Récupère les informations de période."""
        if 'date' not in df.columns:
            return "N/A"
        
        df_copy = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_copy['date']):
            df_copy['date'] = pd.to_datetime(df_copy['date'])
        
        min_date = df_copy['date'].min().strftime("%d/%m/%Y")
        max_date = df_copy['date'].max().strftime("%d/%m/%Y")
        
        return f"{min_date} - {max_date}"
    
    def _render_template(self, **kwargs) -> str:
        """Rend le template HTML avec les données."""
        from jinja2 import Template
        template = Template(self.HTML_TEMPLATE)
        return template.render(**kwargs)
    
    def export_to_excel(
        self,
        df: pd.DataFrame,
        output_path: str,
        sheets: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Path:
        """
        Exporte les données vers Excel avec plusieurs feuilles.
        
        Args:
            df: DataFrame principal
            output_path: Chemin de sortie
            sheets: Dict {nom_feuille: dataframe}
            
        Returns:
            Path: Chemin du fichier Excel
        """
        logger.info(f"Export Excel: {output_path}")
        
        output_path = Path(output_path).with_suffix('.xlsx')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Feuille principale
            df.to_excel(writer, sheet_name='Données', index=False)
            
            # Feuilles supplémentaires
            if sheets:
                for sheet_name, sheet_df in sheets.items():
                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        logger.info(f"Excel généré: {output_path}")
        return output_path
