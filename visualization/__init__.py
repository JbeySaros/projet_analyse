"""
Module visualization - Couche de visualisation.

Ce module gère la création de graphiques et la génération de rapports
professionnels en HTML/PDF.

Classes principales:
    - ChartBuilder: Création de graphiques interactifs et statiques
    - ReportGenerator: Génération de rapports complets

Types de graphiques supportés:
    - Bar charts (vertical/horizontal)
    - Line charts
    - Pie charts / Donuts
    - Scatter plots
    - Heatmaps
    - Histograms
    - Box plots
    - Dashboards multi-graphiques

Formats de sortie:
    - HTML (interactif avec Plotly)
    - PNG/JPG (statique avec Matplotlib)
    - PDF (rapports et graphiques)
    - Excel (données tabulaires)

Usage:
    >>> from visualization import ChartBuilder, ReportGenerator
    >>> 
    >>> # Créer un graphique
    >>> builder = ChartBuilder()
    >>> fig = builder.create_bar_chart(df, x='categorie', y='ca')
    >>> builder.save_chart(fig, 'output/chart.html')
    >>> 
    >>> # Générer un rapport
    >>> generator = ReportGenerator()
    >>> report_path = generator.generate_sales_report(
    ...     df,
    ...     output_path='rapport.html',
    ...     format='html'
    ... )
"""

__version__ = "1.0.0"
__author__ = "Data Analysis Team"

from visualization.chart_builder import ChartBuilder
from visualization.report_generator import ReportGenerator

__all__ = [
    "ChartBuilder",
    "ReportGenerator",
]
