"""
Module de création de graphiques professionnels.
Support Plotly (interactif) et Matplotlib (statique).
"""
from typing import List, Optional, Dict, Union, Literal
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
from config import settings
from utils.logger import get_logger, PerformanceLogger


logger = get_logger(__name__)

# Configuration Matplotlib pour éviter les warnings
matplotlib.use('Agg')


class ChartBuilder:
    """
    Classe pour créer des graphiques professionnels.
    
    Features:
    - Graphiques interactifs avec Plotly
    - Graphiques statiques avec Matplotlib
    - Multiples types de visualisations
    - Personnalisation avancée
    - Export en différents formats
    
    Example:
        >>> builder = ChartBuilder()
        >>> fig = builder.create_bar_chart(df, x='categorie', y='ca_total')
        >>> builder.save_chart(fig, 'output/bar_chart.html')
    """
    
    def __init__(
        self,
        theme: str = None,
        width: int = None,
        height: int = None
    ):
        """
        Initialise le chart builder.
        
        Args:
            theme: Thème des graphiques
            width: Largeur par défaut
            height: Hauteur par défaut
        """
        self.theme = theme or settings.CHART_THEME
        self.width = width or settings.CHART_WIDTH
        self.height = height or settings.CHART_HEIGHT
        
        # Configuration Seaborn pour Matplotlib
        sns.set_style("whitegrid")
        sns.set_palette("husl")
        
        logger.info(
            f"ChartBuilder initialisé - theme={self.theme}, "
            f"size=({self.width}x{self.height})"
        )
    
    def create_bar_chart(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        title: str = "Bar Chart",
        color: Optional[str] = None,
        orientation: Literal['v', 'h'] = 'v',
        use_plotly: bool = True
    ) -> Union[go.Figure, plt.Figure]:
        """
        Crée un graphique en barres.
        
        Args:
            df: DataFrame
            x: Colonne pour l'axe X
            y: Colonne pour l'axe Y
            title: Titre du graphique
            color: Colonne pour la couleur
            orientation: 'v' (vertical) ou 'h' (horizontal)
            use_plotly: True pour Plotly, False pour Matplotlib
            
        Returns:
            Figure: Graphique Plotly ou Matplotlib
            
        Example:
            >>> fig = builder.create_bar_chart(
            ...     df, x='categorie', y='ca_total', title='Ventes par catégorie'
            ... )
        """
        logger.info(f"Création bar chart: {x} vs {y}")
        
        if use_plotly:
            fig = px.bar(
                df,
                x=x,
                y=y,
                color=color,
                title=title,
                orientation=orientation,
                template=self.theme
            )
            fig.update_layout(width=self.width, height=self.height)
            return fig
        else:
            fig, ax = plt.subplots(figsize=(self.width/100, self.height/100))
            
            if orientation == 'v':
                ax.bar(df[x], df[y])
                ax.set_xlabel(x)
                ax.set_ylabel(y)
                plt.xticks(rotation=45, ha='right')
            else:
                ax.barh(df[x], df[y])
                ax.set_xlabel(y)
                ax.set_ylabel(x)
            
            ax.set_title(title)
            plt.tight_layout()
            return fig
    
    def create_line_chart(
        self,
        df: pd.DataFrame,
        x: str,
        y: Union[str, List[str]],
        title: str = "Line Chart",
        markers: bool = True,
        use_plotly: bool = True
    ) -> Union[go.Figure, plt.Figure]:
        """
        Crée un graphique en ligne (courbe).
        
        Args:
            df: DataFrame
            x: Colonne pour l'axe X (généralement temps)
            y: Colonne(s) pour l'axe Y
            title: Titre
            markers: Afficher les marqueurs
            use_plotly: True pour Plotly
            
        Returns:
            Figure: Graphique
            
        Example:
            >>> fig = builder.create_line_chart(
            ...     df, x='date', y='ca_total', title='Évolution des ventes'
            ... )
        """
        logger.info(f"Création line chart: {x} vs {y}")
        
        if use_plotly:
            fig = px.line(
                df,
                x=x,
                y=y,
                title=title,
                markers=markers,
                template=self.theme
            )
            fig.update_layout(width=self.width, height=self.height)
            return fig
        else:
            fig, ax = plt.subplots(figsize=(self.width/100, self.height/100))
            
            if isinstance(y, list):
                for col in y:
                    marker = 'o' if markers else None
                    ax.plot(df[x], df[col], marker=marker, label=col)
                ax.legend()
            else:
                marker = 'o' if markers else None
                ax.plot(df[x], df[y], marker=marker)
            
            ax.set_xlabel(x)
            ax.set_ylabel('Value')
            ax.set_title(title)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            return fig
    
    def create_pie_chart(
        self,
        df: pd.DataFrame,
        names: str,
        values: str,
        title: str = "Pie Chart",
        hole: float = 0,
        use_plotly: bool = True
    ) -> Union[go.Figure, plt.Figure]:
        """
        Crée un graphique en camembert.
        
        Args:
            df: DataFrame
            names: Colonne pour les labels
            values: Colonne pour les valeurs
            title: Titre
            hole: Taille du trou central (0=pie, >0=donut)
            use_plotly: True pour Plotly
            
        Returns:
            Figure: Graphique
            
        Example:
            >>> fig = builder.create_pie_chart(
            ...     df, names='categorie', values='ca_total',
            ...     title='Répartition du CA'
            ... )
        """
        logger.info(f"Création pie chart: {names} / {values}")
        
        if use_plotly:
            fig = px.pie(
                df,
                names=names,
                values=values,
                title=title,
                hole=hole,
                template=self.theme
            )
            fig.update_layout(width=self.width, height=self.height)
            return fig
        else:
            fig, ax = plt.subplots(figsize=(self.width/100, self.height/100))
            
            if hole > 0:
                wedges, texts, autotexts = ax.pie(
                    df[values],
                    labels=df[names],
                    autopct='%1.1f%%',
                    startangle=90,
                    wedgeprops=dict(width=1-hole)
                )
            else:
                wedges, texts, autotexts = ax.pie(
                    df[values],
                    labels=df[names],
                    autopct='%1.1f%%',
                    startangle=90
                )
            
            ax.set_title(title)
            plt.tight_layout()
            return fig
    
    def create_scatter_plot(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        title: str = "Scatter Plot",
        color: Optional[str] = None,
        size: Optional[str] = None,
        trendline: bool = False,
        use_plotly: bool = True
    ) -> Union[go.Figure, plt.Figure]:
        """
        Crée un nuage de points.
        
        Args:
            df: DataFrame
            x: Colonne X
            y: Colonne Y
            title: Titre
            color: Colonne pour la couleur
            size: Colonne pour la taille des points
            trendline: Afficher la ligne de tendance
            use_plotly: True pour Plotly
            
        Returns:
            Figure: Graphique
        """
        logger.info(f"Création scatter plot: {x} vs {y}")
        
        if use_plotly:
            trendline_param = 'ols' if trendline else None
            fig = px.scatter(
                df,
                x=x,
                y=y,
                color=color,
                size=size,
                title=title,
                trendline=trendline_param,
                template=self.theme
            )
            fig.update_layout(width=self.width, height=self.height)
            return fig
        else:
            fig, ax = plt.subplots(figsize=(self.width/100, self.height/100))
            
            if color and color in df.columns:
                scatter = ax.scatter(df[x], df[y], c=df[color], cmap='viridis', alpha=0.6)
                plt.colorbar(scatter, ax=ax, label=color)
            else:
                ax.scatter(df[x], df[y], alpha=0.6)
            
            if trendline:
                z = np.polyfit(df[x], df[y], 1)
                p = np.poly1d(z)
                ax.plot(df[x], p(df[x]), "r--", alpha=0.8, label='Tendance')
                ax.legend()
            
            ax.set_xlabel(x)
            ax.set_ylabel(y)
            ax.set_title(title)
            plt.tight_layout()
            return fig
    
    def create_heatmap(
        self,
        df: pd.DataFrame,
        title: str = "Heatmap",
        annotate: bool = True,
        use_plotly: bool = True
    ) -> Union[go.Figure, plt.Figure]:
        """
        Crée une heatmap (carte thermique).
        
        Args:
            df: DataFrame ou matrice de corrélation
            title: Titre
            annotate: Afficher les valeurs dans les cellules
            use_plotly: True pour Plotly
            
        Returns:
            Figure: Graphique
            
        Example:
            >>> corr_matrix = df.corr()
            >>> fig = builder.create_heatmap(corr_matrix, title='Corrélations')
        """
        logger.info("Création heatmap")
        
        if use_plotly:
            fig = go.Figure(data=go.Heatmap(
                z=df.values,
                x=df.columns.tolist(),
                y=df.index.tolist(),
                colorscale='RdBu_r',
                zmid=0,
                text=df.values if annotate else None,
                texttemplate='%{text:.2f}' if annotate else None
            ))
            
            fig.update_layout(
                title=title,
                width=self.width,
                height=self.height,
                template=self.theme
            )
            return fig
        else:
            fig, ax = plt.subplots(figsize=(self.width/100, self.height/100))
            
            sns.heatmap(
                df,
                annot=annotate,
                fmt='.2f',
                cmap='RdBu_r',
                center=0,
                ax=ax,
                cbar_kws={'label': 'Correlation'}
            )
            
            ax.set_title(title)
            plt.tight_layout()
            return fig
    
    def create_histogram(
        self,
        df: pd.DataFrame,
        column: str,
        title: str = "Histogram",
        bins: int = 30,
        show_kde: bool = True,
        use_plotly: bool = True
    ) -> Union[go.Figure, plt.Figure]:
        """
        Crée un histogramme.
        
        Args:
            df: DataFrame
            column: Colonne à visualiser
            title: Titre
            bins: Nombre de bins
            show_kde: Afficher la courbe de densité
            use_plotly: True pour Plotly
            
        Returns:
            Figure: Graphique
        """
        logger.info(f"Création histogram: {column}")
        
        if use_plotly:
            fig = px.histogram(
                df,
                x=column,
                nbins=bins,
                title=title,
                template=self.theme
            )
            fig.update_layout(width=self.width, height=self.height)
            return fig
        else:
            fig, ax = plt.subplots(figsize=(self.width/100, self.height/100))
            
            ax.hist(df[column].dropna(), bins=bins, alpha=0.7, edgecolor='black')
            
            if show_kde:
                from scipy import stats
                data = df[column].dropna()
                kde = stats.gaussian_kde(data)
                x_range = np.linspace(data.min(), data.max(), 100)
                
                # Scale KDE to match histogram
                ax2 = ax.twinx()
                ax2.plot(x_range, kde(x_range), 'r-', linewidth=2, label='KDE')
                ax2.set_ylabel('Densité')
                ax2.legend()
            
            ax.set_xlabel(column)
            ax.set_ylabel('Fréquence')
            ax.set_title(title)
            plt.tight_layout()
            return fig
    
    def create_box_plot(
        self,
        df: pd.DataFrame,
        y: str,
        x: Optional[str] = None,
        title: str = "Box Plot",
        use_plotly: bool = True
    ) -> Union[go.Figure, plt.Figure]:
        """
        Crée un box plot (boîte à moustaches).
        
        Args:
            df: DataFrame
            y: Colonne numérique
            x: Colonne catégorielle (optionnel)
            title: Titre
            use_plotly: True pour Plotly
            
        Returns:
            Figure: Graphique
        """
        logger.info(f"Création box plot: {y}")
        
        if use_plotly:
            fig = px.box(
                df,
                x=x,
                y=y,
                title=title,
                template=self.theme
            )
            fig.update_layout(width=self.width, height=self.height)
            return fig
        else:
            fig, ax = plt.subplots(figsize=(self.width/100, self.height/100))
            
            if x:
                df.boxplot(column=y, by=x, ax=ax)
            else:
                df.boxplot(column=y, ax=ax)
            
            ax.set_title(title)
            plt.suptitle('')  # Supprimer le titre auto de pandas
            plt.tight_layout()
            return fig
    
    def create_dashboard(
        self,
        charts: List[Dict],
        title: str = "Dashboard",
        rows: int = 2,
        cols: int = 2
    ) -> go.Figure:
        """
        Crée un dashboard avec plusieurs graphiques.
        
        Args:
            charts: Liste de dict avec {type, data, config}
            title: Titre du dashboard
            rows: Nombre de lignes
            cols: Nombre de colonnes
            
        Returns:
            go.Figure: Dashboard Plotly
            
        Example:
            >>> charts = [
            ...     {'type': 'bar', 'data': df1, 'x': 'cat', 'y': 'val'},
            ...     {'type': 'line', 'data': df2, 'x': 'date', 'y': 'sales'}
            ... ]
            >>> dashboard = builder.create_dashboard(charts, rows=1, cols=2)
        """
        logger.info(f"Création dashboard: {rows}x{cols} = {len(charts)} graphiques")
        
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=[c.get('title', f'Chart {i+1}') for i, c in enumerate(charts)]
        )
        
        for i, chart_config in enumerate(charts):
            row = (i // cols) + 1
            col = (i % cols) + 1
            
            # Créer le graphique selon le type
            # (Implémentation simplifiée - à étendre selon les besoins)
            chart_type = chart_config.get('type', 'bar')
            
            if chart_type == 'bar':
                fig.add_trace(
                    go.Bar(x=chart_config['data'][chart_config['x']],
                           y=chart_config['data'][chart_config['y']]),
                    row=row, col=col
                )
        
        fig.update_layout(
            title_text=title,
            showlegend=False,
            height=self.height * rows,
            width=self.width
        )
        
        return fig
    
    def save_chart(
        self,
        fig: Union[go.Figure, plt.Figure],
        filepath: Union[str, Path],
        format: str = 'auto'
    ):
        """
        Sauvegarde un graphique.
        
        Args:
            fig: Figure Plotly ou Matplotlib
            filepath: Chemin de sauvegarde
            format: Format ('html', 'png', 'pdf', 'svg', 'auto')
            
        Example:
            >>> builder.save_chart(fig, 'output/chart.html')
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'auto':
            format = filepath.suffix.lstrip('.')
        
        logger.info(f"Sauvegarde graphique: {filepath} (format={format})")
        
        if isinstance(fig, go.Figure):
            # Plotly
            if format == 'html':
                fig.write_html(str(filepath))
            elif format in ['png', 'jpg', 'jpeg']:
                fig.write_image(str(filepath))
            elif format == 'pdf':
                fig.write_image(str(filepath), format='pdf')
            else:
                fig.write_html(str(filepath))
        else:
            # Matplotlib
            fig.savefig(str(filepath), format=format, dpi=settings.CHART_DPI, bbox_inches='tight')
        
        logger.info(f"Graphique sauvegardé: {filepath}")
