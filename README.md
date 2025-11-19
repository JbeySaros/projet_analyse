# 📊 Data Analysis Platform - Plateforme d'Analyse de Données

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

[![Jenkins](https://img.shields.io/badge/Jenkins-D24939?logo=jenkins&logoColor=white)](https://www.jenkins.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)](https://redis.io/)

> Plateforme SaaS complète pour l'ingestion, le traitement et l'analyse de données de ventes multi-sources avec génération de rapports interactifs.

---

##  Vue d'Ensemble

Cette plateforme d'analyse de données est conçue comme un système **robuste**, **scalable** et **maintenable** permettant de :

-  Ingérer et traiter des volumes croissants de données CSV
-  Fournir une API REST pour accéder aux données et résultats d'analyse
-  Générer des rapports visuels interactifs (graphiques, dashboards)
-  Gérer les erreurs et performances à grande échelle
-  Documenter et tester le code pour une équipe de développeurs

###  Architecture

```
projet_analyse/
├── data_loader/             # Couche d'entrée des données
│   ├── csv_loader.py        # Chargement CSV avec Repository Pattern
│   ├── data_validator.py    # Validation des données
│   └── exceptions.py        # Exceptions personnalisées
│
├── data_processor/          # Couche de traitement
│   ├── cleaner.py           # Nettoyage avancé (outliers, imputation)
│   ├── aggregator.py        # Agrégations complexes et KPIs
│   └── statistics.py        # Statistiques descriptives et inférentielles
│
├── visualization/           # Couche de visualisation
│   ├── chart_builder.py     # Création de graphiques (Plotly/Matplotlib)
│   └── report_generator.py  # Génération de rapports HTML/PDF
│
├── api/                     # API REST FastAPI
│   └── main.py              # Endpoints et routes
│
├── tests/                   # Tests unitaires et d'intégration
│   └── test_loader.py       # Exemple de tests avec pytest
│
├── utils/                   # Utilitaires
│   └── logger.py            # Logging professionnel
│
├── config.py                # Configuration centralisée
├── main.py                  # Point d'entrée du pipeline
├── requirements.txt         # Dépendances Python
└── README.md                # Documentation
```

---

##  Installation

### Prérequis

- **Python 3.10+**
- **pip** ou **poetry**
- **Redis** (optionnel, pour le cache)
- **Docker** (optionnel, pour la conteneurisation)

### Installation Locale

1. **Cloner le repository**

```bash
git clone https://github.com/votre-username/data-analysis-platform.git
cd data-analysis-platform
```

2. **Créer un environnement virtuel**

```bash
python -m venv venv

# Activation
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Installer les dépendances**

```bash
pip install -r requirements.txt
```

4. **Configurer les variables d'environnement**

```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

5. **Créer les répertoires nécessaires**

```bash
mkdir -p data uploads outputs logs
```

---

##  Utilisation

### 1. Pipeline en Ligne de Commande

Analyse complète d'un fichier CSV :

```bash
python main.py data/vente_2025.csv -o outputs/
```

**Options disponibles :**

```bash
python main.py --help

Options:
  -o, --output DIR        Répertoire de sortie (défaut: outputs)
  --skip-cleaning         Ignorer l'étape de nettoyage
  --skip-validation       Ignorer la validation
  --no-report             Ne pas générer le rapport HTML/PDF
  --no-excel              Ne pas exporter en Excel
```

**Exemple complet :**

```bash
python main.py data/vente_2025.csv \
    --output resultats_janvier \
    --skip-validation
```

### 2. API REST

#### Démarrage de l'API

```bash
# Mode développement
python api/main.py

# Ou avec uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Documentation Interactive

Une fois l'API lancée, accédez à :

- **Swagger UI** : http://localhost:8000/api/docs
- **ReDoc** : http://localhost:8000/api/redoc

#### Endpoints Principaux

#####  Upload de fichier

```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@data/vente_2025.csv" \
  -F "validate=true"
```

#####  Analyse complète

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@data/vente_2025.csv" \
  -F "clean=true" \
  -F "remove_outliers=false"
```

#####  Génération de graphique

```bash
curl -X POST "http://localhost:8000/api/v1/charts/bar" \
  -F "file=@data/vente_2025.csv" \
  -F "x=categorie" \
  -F "y=ca_total" \
  -F "title=Ventes par Catégorie"
```

#####  Génération de rapport

```bash
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -F "file=@data/vente_2025.csv" \
  -F "format=html" \
  --output rapport.html
```

#####  Statistiques

```bash
# Statistiques descriptives
curl -X POST "http://localhost:8000/api/v1/stats/describe" \
  -F "file=@data/vente_2025.csv"

# Matrice de corrélation
curl -X POST "http://localhost:8000/api/v1/stats/correlation" \
  -F "file=@data/vente_2025.csv" \
  -F "method=pearson"
```

### 3. Utilisation Programmatique

```python
from main import DataAnalysisPipeline

# Créer une instance du pipeline
pipeline = DataAnalysisPipeline()

# Exécuter l'analyse complète
success = pipeline.run(
    file_path="data/vente_2025.csv",
    output_dir="outputs/",
    skip_cleaning=False,
    generate_report=True,
    export_excel=True
)

if success:
    print("✓ Analyse terminée avec succès")
```

**Utilisation modulaire :**

```python
from data_loader.csv_loader import CSVLoader
from data_processor.aggregator import DataAggregator
from visualization.chart_builder import ChartBuilder

# Charger les données
loader = CSVLoader()
df = loader.load("data/vente_2025.csv")

# Calculer les KPIs
aggregator = DataAggregator()
kpis = aggregator.calculate_kpis(df)
print(f"CA Total: {kpis['revenue_total']:.2f}€")

# Créer un graphique
builder = ChartBuilder()
fig = builder.create_bar_chart(df, x='categorie', y='prix')
builder.save_chart(fig, "output/chart.html")
```

---

##  Tests

### Exécuter tous les tests

```bash
pytest
```

### Tests avec couverture

```bash
pytest --cov=data_loader --cov=data_processor --cov=visualization \
       --cov-report=html --cov-report=term-missing
```

### Tests par catégorie

```bash
# Tests unitaires uniquement
pytest -m unit

# Tests d'intégration
pytest -m integration

# Tests d'un module spécifique
pytest tests/test_loader.py -v
```

### Rapport de couverture

Après exécution avec `--cov-report=html`, ouvrez :

```bash
open htmlcov/index.html  # Mac/Linux
start htmlcov/index.html # Windows
```

---

##  Fonctionnalités Détaillées

###  Chargement de Données

- **Formats supportés** : CSV, Excel (XLSX, XLS)
- **Détection automatique** : Encodage et délimiteur
- **Gros fichiers** : Chargement par chunks
- **Validation** : Types, valeurs manquantes, doublons
- **Logging** : Traçabilité complète

```python
from data_loader.csv_loader import CSVLoader

loader = CSVLoader()
df = loader.load("data/vente_2025.csv")
# ✓ Données chargées: 10,000 lignes, 7 colonnes
```

###  Nettoyage de Données

- **Outliers** : Détection IQR et Z-score
- **Imputation** : Mean, Median, KNN, Forward/Backward Fill
- **Normalisation** : Standard Scaler, MinMax, Robust
- **Encodage** : Label Encoding, One-Hot Encoding

```python
from data_processor.cleaner import DataCleaner

cleaner = DataCleaner()
df_clean = cleaner.clean(
    df,
    remove_outliers=True,
    impute_missing=True,
    normalize=False
)
```

###  Agrégations et KPIs

- **Groupby multi-niveaux**
- **Pivots et cross-tabs**
- **Time-series resampling**
- **KPIs métier** : CA, panier moyen, top produits

```python
from data_processor.aggregator import DataAggregator

aggregator = DataAggregator()
kpis = aggregator.calculate_kpis(df)
sales_by_category = aggregator.calculate_sales_by_category(df)
```

###  Statistiques

- **Descriptives** : Mean, std, quartiles, skewness, kurtosis
- **Inférentielles** : T-test, Chi2, intervalles de confiance
- **Corrélations** : Pearson, Spearman, Kendall
- **Tests de normalité** : Shapiro-Wilk, Kolmogorov-Smirnov

```python
from data_processor.statistics import StatisticsCalculator

stats = StatisticsCalculator()
summary = stats.describe_column(df, 'prix')
corr_matrix = stats.calculate_correlation_matrix(df)
```

###  Visualisations

**Types de graphiques** :
- Bar charts (vertical/horizontal)
- Line charts (courbes)
- Pie charts / Donuts
- Scatter plots (avec trendline)
- Heatmaps (corrélations)
- Histograms (distributions)
- Box plots

```python
from visualization.chart_builder import ChartBuilder

builder = ChartBuilder()

# Graphique en barres
fig = builder.create_bar_chart(df, x='categorie', y='ca_total')
builder.save_chart(fig, 'output/bar_chart.html')

# Évolution temporelle
fig = builder.create_line_chart(df, x='date', y='ca')
```

###  Génération de Rapports

- **Formats** : HTML (interactif), PDF
- **Contenu** : KPIs, tableaux, graphiques, statistiques
- **Templates** : Personnalisables avec Jinja2
- **Export** : Excel multi-feuilles

```python
from visualization.report_generator import ReportGenerator

generator = ReportGenerator()
report_path = generator.generate_sales_report(
    df,
    output_path='rapport.html',
    format='html',
    include_charts=True
)
```

---

## Patterns et Principes

### Design Patterns Implémentés

1. **Repository Pattern** : Abstraction de l'accès aux données
2. **Factory Pattern** : Création d'objets (charts, loaders)
3. **Strategy Pattern** : Algorithmes interchangeables (cleaning)
4. **Singleton** : Logger, Configuration
5. **Dependency Injection** : FastAPI Depends()

### Principes SOLID

-  **Single Responsibility** : Chaque classe a un rôle unique
-  **Open/Closed** : Extensible sans modification
-  **Liskov Substitution** : Interfaces cohérentes
-  **Interface Segregation** : Interfaces spécifiques
-  **Dependency Inversion** : Dépendances abstraites

### Clean Code

-  **PEP 8** : Conformité au style Python
-  **Type Hints** : Typage statique avec mypy
-  **Docstrings** : Documentation complète (Google style)
-  **DRY** : Don't Repeat Yourself
-  **KISS** : Keep It Stupid Simple

---

## 🔧 Configuration

Toute la configuration est centralisée dans `config.py` et peut être surchargée via variables d'environnement (`.env`).

### Paramètres Principaux

```python
# Voir config.py pour la liste complète

# Taille max des fichiers
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

# Méthode de détection des outliers
OUTLIER_METHOD = "iqr"  # ou "zscore"

# Cache Redis
CACHE_TTL = 3600  # 1 heure
CACHE_ENABLED = True

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

---

##  Documentation API

### Modèles de Données

#### Upload Response

```json
{
  "success": true,
  "filename": "vente_2025.csv",
  "rows": 1000,
  "columns": 7,
  "column_names": ["date", "produit", "categorie", "prix", "quantite", "ville", "source"],
  "memory_mb": 0.5,
  "validation": {
    "is_valid": true,
    "errors": [],
    "warnings": []
  }
}
```

#### KPIs Response

```json
{
  "revenue_total": 125000.50,
  "transaction_count": 1000,
  "average_basket": 125.00,
  "total_quantity": 5000,
  "average_price": 25.00,
  "unique_products": 50,
  "unique_categories": 5,
  "unique_cities": 10
}
```

---

##  Docker

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
    volumes:
      - ./data:/app/data
      - ./outputs:/app/outputs
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Commandes

```bash
# Build et démarrage
docker-compose up -d

# Logs
docker-compose logs -f api

# Arrêt
docker-compose down
```

---

## 📝 Licence

Ce projet est sous licence GNU GPL v3


