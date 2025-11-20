"""
Module de génération de rapports complets (HTML/PDF).
Agrège données, statistiques et visualisations.
"""

from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd

from jinja2 import Template
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from config import settings
from utils.logger import get_logger, PerformanceLogger
from visualization.chart_builder import ChartBuilder
from data_processor.statistics import StatisticsCalculator
from data_processor.aggregator import DataAggregator

logger = get_logger(__name__)


class ReportGenerator:
    HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{ title }}</title>

    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: "DejaVu Sans", sans-serif;
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
            font-size: 2.4em;
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
                <p>Généré le {{ date }} | Période : {{ period }}</p>
                <p>Données : {{ data_info }}</p>
            </div>
        </header>

        <section>
            <h2>Indicateurs Clés de Performance (KPIs)</h2>
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
        self.chart_builder = ChartBuilder()
        self.stats_calc = StatisticsCalculator()
        self.aggregator = DataAggregator()
        self.font_config = FontConfiguration()

        logger.info("ReportGenerator initialisé")

    # -------------------------------------------------------------
    # MÉTHODE PRINCIPALE DE GÉNÉRATION
    # -------------------------------------------------------------
    def generate_sales_report(
        self,
        df: pd.DataFrame,
        output_path: str,
        format: str = "html",
        include_charts: bool = True
    ) -> Path:
        """
        Génère un rapport complet sur les ventes.
        """

        with PerformanceLogger(logger, "generate_sales_report"):
            logger.info(f"Génération rapport ventes (format={format})")

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if "revenue" not in df.columns and "prix" in df.columns and "quantite" in df.columns:
                df["revenue"] = df["prix"] * df["quantite"]

            kpis = self._prepare_kpis(df)

            content_sections = []
            content_sections.append(self._generate_overview_section(df))
            content_sections.append(self._generate_category_analysis(df, include_charts))
            content_sections.append(self._generate_geographic_analysis(df, include_charts))

            if "date" in df.columns:
                content_sections.append(self._generate_temporal_analysis(df, include_charts))

            content_sections.append(self._generate_top_products_section(df))
            content_sections.append(self._generate_statistics_section(df))

            content = "\n".join(content_sections)

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

            # Export HTML
            if format == "html":
                output_html = output_path.with_suffix(".html")
                output_html.write_text(html_content, encoding="utf-8")
                logger.info(f"Rapport HTML généré : {output_html}")
                return output_html

            # Export PDF
            if format == "pdf":
                output_pdf = output_path.with_suffix(".pdf")

                css = CSS(string="""
                    body { font-family: "DejaVu Sans", sans-serif; }
                """)

                HTML(string=html_content, base_url=str(Path.cwd())).write_pdf(
                    output_pdf,
                    stylesheets=[css],
                    font_config=self.font_config
                )

                logger.info(f"Rapport PDF généré : {output_pdf}")
                return output_pdf

            raise ValueError("Format non supporté : doit être 'html' ou 'pdf'")

    # -------------------------------------------------------------
    # SECTIONS DU RAPPORT
    # -------------------------------------------------------------
    def _prepare_kpis(self, df: pd.DataFrame) -> List[Dict]:
        kpis_data = self.aggregator.calculate_kpis(df)

        return [
            {"label": "Chiffre d'Affaires Total", "value": f"{kpis_data.get('revenue_total', 0):,.2f} €"},
            {"label": "Nombre de Transactions", "value": f"{kpis_data.get('transaction_count', 0):,}"},
            {"label": "Panier Moyen", "value": f"{kpis_data.get('average_basket', 0):.2f} €"},
            {"label": "Quantité Totale", "value": f"{kpis_data.get('total_quantity', 0):,}"},
        ]

    def _generate_overview_section(self, df: pd.DataFrame) -> str:
        html = "<section>\n<h2>Vue d'Ensemble</h2>\n"

        info = f"""
        <div class="info">
            <h3>Informations Générales</h3>
            <ul>
                <li><strong>Nombre de transactions :</strong> {len(df):,}</li>
                <li><strong>Produits uniques :</strong> {df['produit'].nunique() if 'produit' in df.columns else 'N/A'}</li>
                <li><strong>Catégories :</strong> {df['categorie'].nunique() if 'categorie' in df.columns else 'N/A'}</li>
                <li><strong>Villes :</strong> {df['ville'].nunique() if 'ville' in df.columns else 'N/A'}</li>
            </ul>
        </div>
        """
        html += info
        html += "</section>\n"
        return html

    def _generate_category_analysis(self, df: pd.DataFrame, include_charts: bool) -> str:
        html = "<section>\n<h2>Analyse par Catégorie</h2>\n"

        if "categorie" not in df.columns:
            return html + "<p>Données de catégorie non disponibles.</p></section>\n"

        cat_sales = self.aggregator.calculate_sales_by_category(df)

        html += "<h3>Ventes par Catégorie</h3>\n"
        html += cat_sales.to_html(index=False, classes="table", float_format="%.2f")

        if include_charts:
            fig = self.chart_builder.create_bar_chart(
                cat_sales, x="categorie", y="ca_total", title="Chiffre d'Affaires par Catégorie"
            )
            html += f'<div class="chart-container">{fig.to_html(include_plotlyjs="cdn")}</div>\n'

        html += "</section>\n"
        return html

    def _generate_geographic_analysis(self, df: pd.DataFrame, include_charts: bool) -> str:
        html = "<section>\n<h2>Analyse Géographique</h2>\n"

        if "ville" not in df.columns:
            return html + "<p>Données géographiques non disponibles.</p></section>\n"

        city_sales = self.aggregator.calculate_sales_by_city(df)

        html += "<h3>Ventes par Ville</h3>\n"
        html += city_sales.to_html(index=False, classes="table", float_format="%.2f")

        if include_charts:
            fig = self.chart_builder.create_pie_chart(
                city_sales.head(10),
                names="ville",
                values="ca_total",
                title="Répartition du CA par Ville (Top 10)",
                hole=0.3
            )
            html += f'<div class="chart-container">{fig.to_html(include_plotlyjs="cdn")}</div>\n'

        html += "</section>\n"
        return html

    def _generate_temporal_analysis(self, df: pd.DataFrame, include_charts: bool) -> str:
        html = "<section>\n<h2>Analyse Temporelle</h2>\n"

        df_copy = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_copy["date"]):
            df_copy["date"] = pd.to_datetime(df_copy["date"])

        trend = self.aggregator.calculate_trend_analysis(df_copy, "date", period="M")

        html += "<h3>Évolution Mensuelle</h3>\n"
        html += trend.to_html(index=False, classes="table", float_format="%.2f")

        if include_charts:
            fig = self.chart_builder.create_line_chart(
                trend, x="date", y="ca_total", title="Évolution du Chiffre d'Affaires"
            )
            html += f'<div class="chart-container">{fig.to_html(include_plotlyjs="cdn")}</div>\n'

        html += "</section>\n"
        return html

    def _generate_top_products_section(self, df: pd.DataFrame) -> str:
        html = "<section>\n<h2>Top Produits</h2>\n"

        if "produit" not in df.columns:
            return html + "<p>Données produits non disponibles.</p></section>\n"

        top = self.aggregator.calculate_top_products(df, top_n=10)
        html += "<h3>Top 10 Produits par CA</h3>\n"
        html += top.to_html(index=False, classes="table", float_format="%.2f")

        html += "</section>\n"
        return html

    def _generate_statistics_section(self, df: pd.DataFrame) -> str:
        html = "<section>\n<h2>Statistiques Détaillées</h2>\n"

        stats_dict = self.stats_calc.describe_dataframe(df)
        if stats_dict:
            html += "<h3>Statistiques Descriptives</h3>\n"
            stats_df = pd.DataFrame([s.to_dict() for s in stats_dict.values()])
            html += stats_df.to_html(index=False, classes="table", float_format="%.2f")

        html += "</section>\n"
        return html

    # -------------------------------------------------------------
    # UTILITAIRES
    # -------------------------------------------------------------
    def _get_period_info(self, df: pd.DataFrame) -> str:
        if "date" not in df.columns:
            return "N/A"

        df_copy = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_copy["date"]):
            df_copy["date"] = pd.to_datetime(df_copy["date"])

        return f"{df_copy['date'].min().strftime('%d/%m/%Y')} - {df_copy['date'].max().strftime('%d/%m/%Y')}"

    def _render_template(self, **kwargs) -> str:
        template = Template(self.HTML_TEMPLATE)
        return template.render(**kwargs)

    # -------------------------------------------------------------
    # EXPORT EXCEL
    # -------------------------------------------------------------
    def export_to_excel(
        self,
        df: pd.DataFrame,
        output_path: str,
        sheets: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Path:

        output_path = Path(output_path).with_suffix(".xlsx")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Données", index=False)

            if sheets:
                for sheet_name, sheet_df in sheets.items():
                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"Excel généré : {output_path}")
        return output_path
