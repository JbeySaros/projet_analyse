# 🏛️Architecture de la Plateforme

Ce document décrit l'architecture technique, les patterns utilisés et les décisions de conception de la plateforme d'analyse de données.

---

##  Vue d'Ensemble

### Architecture en Couches

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│              Endpoints REST, Authentication, CORS            │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│         Pipeline, Orchestration, Business Logic              │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌────────────────┬─────────────────┬───────────────────────────┐
│  Data Loader   │ Data Processor  │     Visualization         │
│  Repository    │  Cleaner        │     Chart Builder         │
│  Validator     │  Aggregator     │     Report Generator      │
│                │  Statistics     │                           │
└────────────────┴─────────────────┴───────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Infrastructure Layer                            │
│     Config, Logging, Cache (Redis), Storage                  │
└─────────────────────────────────────────────────────────────┘
```

---

##  Design Patterns Implémentés

### 1. Repository Pattern

**Où** : `data_loader/csv_loader.py`

**Pourquoi** : Abstraction de l'accès aux données, facilite l'ajout de nouvelles sources.

```python
class DataLoaderRepository:
    """Abstrait l'accès aux différentes sources de données."""
    
    def load_data(self, file_path, file_format=None):
        if file_format == 'csv':
            return self.csv_loader.load(file_path)
        elif file_format == 'excel':
            return self._load_excel(file_path)
        # Facile d'ajouter JSON, API, Database, etc.
```

**Avantages** :
-  Séparation des responsabilités
-  Testabilité (mocking facile)
-  Extensibilité sans modification du code existant

### 2. Strategy Pattern

**Où** : `data_processor/cleaner.py`

**Pourquoi** : Algorithmes interchangeables pour le nettoyage et l'imputation.

```python
class ImputationStrategy(Enum):
    MEAN = "mean"
    MEDIAN = "median"
    KNN = "knn"

def impute_missing_values(self, df, strategy: ImputationStrategy):
    # Choix de l'algorithme à l'exécution
    if strategy == ImputationStrategy.KNN:
        imputer = KNNImputer()
    else:
        imputer = SimpleImputer(strategy=strategy.value)
```

**Avantages** :
-  Flexibilité dans le choix des algorithmes
-  Code DRY (Don't Repeat Yourself)
-  Facile à étendre

### 3. Factory Pattern

**Où** : `visualization/chart_builder.py`

**Pourquoi** : Création d'objets graphiques de manière centralisée.

```python
class ChartBuilder:
    def create_bar_chart(...):
        # Factory pour bar charts
        
    def create_line_chart(...):
        # Factory pour line charts
        
    # Facile d'ajouter de nouveaux types
```

**Avantages** :
-  Encapsulation de la création d'objets
-  Interface uniforme
-  Configuration centralisée

### 4. Singleton Pattern

**Où** : `utils/logger.py`, `config.py`

**Pourquoi** : Une seule instance du logger et de la configuration.

```python
class LoggerManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**Avantages** :
-  Cohérence globale
-  Économie de ressources
-  Point d'accès unique

### 5. Dependency Injection

**Où** : `api/main.py`

**Pourquoi** : Inversion de contrôle, testabilité.

```python
def get_data_loader():
    return DataLoaderRepository()

@app.post("/upload")
async def upload_file(
    file: UploadFile,
    loader: DataLoaderRepository = Depends(get_data_loader)
):
    # Injection de dépendance par FastAPI
```

**Avantages** :
-  Découplage
-  Testabilité (mocking simple)
-  Flexibilité

---

## Principes SOLID

### Single Responsibility Principle (SRP)

Chaque classe a une responsabilité unique :

- `CSVLoader` : **Uniquement** charger des CSV
- `DataValidator` : **Uniquement** valider
- `DataCleaner` : **Uniquement** nettoyer

### Open/Closed Principle (OCP)

Ouvert à l'extension, fermé à la modification :

```python
# Ajout d'un nouveau type de graphique sans modifier ChartBuilder
class ChartBuilder:
    def create_chart(self, chart_type, ...):
        factory = self._get_factory(chart_type)
        return factory.create(...)
```

### Liskov Substitution Principle (LSP)

Les sous-classes sont substituables :

```python
# Toutes les stratégies d'imputation sont interchangeables
imputer: ImputationStrategy = get_strategy(config)
df = cleaner.impute(df, strategy=imputer)
```

### Interface Segregation Principle (ISP)

Interfaces spécifiques plutôt que génériques :

```python
# Interfaces séparées pour différents besoins
class IDataLoader:
    def load(self, path): pass

class IDataValidator:
    def validate(self, df): pass
```

### Dependency Inversion Principle (DIP)

Dépendre d'abstractions, pas d'implémentations :

```python
# Pipeline dépend d'interfaces, pas d'implémentations concrètes
class DataAnalysisPipeline:
    def __init__(self, loader: IDataLoader, cleaner: IDataCleaner):
        self.loader = loader
        self.cleaner = cleaner
```

---

##  Flux de Données

### Pipeline Complet

```
┌──────────────┐
│  CSV File    │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  CSVLoader       │  ← Repository Pattern
│  - Détection     │
│  - Validation    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  DataValidator   │  ← Strategy Pattern
│  - Types         │
│  - Missing       │
│  - Duplicates    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  DataCleaner     │  ← Strategy Pattern
│  - Outliers      │
│  - Imputation    │
│  - Normalization │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  DataAggregator  │
│  - Groupby       │
│  - KPIs          │
│  - Time Series   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Statistics      │
│  - Descriptive   │
│  - Inferential   │
│  - Correlation   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  ChartBuilder    │  ← Factory Pattern
│  - Bar           │
│  - Line          │
│  - Pie, etc.     │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  ReportGenerator │
│  - HTML          │
│  - PDF           │
│  - Excel         │
└──────────────────┘
```

---

## Gestion des Données

### Cache Strategy (Redis)

```python
# Pattern: Cache-Aside
def get_aggregation(key):
    # 1. Vérifier le cache
    cached = redis.get(key)
    if cached:
        return cached
    
    # 2. Calculer si absent
    result = compute_aggregation()
    
    # 3. Mettre en cache
    redis.set(key, result, ex=TTL)
    
    return result
```

### File Storage

```
data/           # Sources (read-only)
uploads/        # Temporaire (auto-cleanup)
outputs/        # Résultats (persistants)
logs/           # Logs rotatifs
```

---

##  Sécurité

### Validation des Entrées

```python
# 1. Validation du format
if file_ext not in ALLOWED_EXTENSIONS:
    raise InvalidFileFormatError()

# 2. Validation de la taille
if file_size > MAX_FILE_SIZE:
    raise FileSizeExceededError()

# 3. Validation du contenu
result = validator.validate(df)
if not result.is_valid:
    raise ValidationError()
```

### Rate Limiting (API)

```python
@app.post("/api/v1/upload")
@limiter.limit("100/minute")
async def upload_file(...):
    # Protégé contre les abus
```

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

##  Performance

### Optimisations Implémentées

#### 1. Chunked Loading

```python
# Pour les gros fichiers
def _load_in_chunks(self, file_path, chunk_size=10000):
    chunks = pd.read_csv(file_path, chunksize=chunk_size)
    return pd.concat(chunks, ignore_index=True)
```

#### 2. Vectorisation NumPy

```python
# Éviter les boucles Python
#  Lent
for i in range(len(df)):
    df.loc[i, 'result'] = df.loc[i, 'a'] * df.loc[i, 'b']

#  Rapide (vectorisé)
df['result'] = df['a'] * df['b']
```

#### 3. Cache Redis

```python
# Mise en cache des résultats coûteux
@cache_result(ttl=3600)
def calculate_complex_aggregation(df):
    # Calcul lourd mis en cache
```

#### 4. Lazy Loading

```python
# Chargement à la demande
class Pipeline:
    @property
    def aggregator(self):
        if not hasattr(self, '_aggregator'):
            self._aggregator = DataAggregator()
        return self._aggregator
```

---

##  Testabilité

### Architecture Testable

```python
# 1. Injection de dépendances
def test_pipeline():
    mock_loader = Mock(spec=DataLoaderRepository)
    pipeline = DataAnalysisPipeline(loader=mock_loader)
    
# 2. Interfaces claires
def test_validator():
    validator = DataValidator()
    result = validator.validate(test_df)
    assert result.is_valid

# 3. Fixtures réutilisables
@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({...})
```

### Couverture de Tests

```
data_loader/     → 85%
data_processor/  → 80%
visualization/   → 75%
api/             → 70%
```

---

##  Déploiement

### Docker Multi-Stage Build

```dockerfile
# Stage 1: Builder (dépendances)
FROM python:3.11-slim as builder
RUN pip install --user -r requirements.txt

# Stage 2: Runtime (léger)
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY . /app
CMD ["uvicorn", "api.main:app"]
```

### Orchestration

```yaml
# docker-compose.yml
services:
  api:      # Application principale
  redis:    # Cache
  nginx:    # Reverse proxy (optionnel)
```

---

##  Scalabilité

### Horizontal Scaling

```yaml
# Plusieurs workers API
api:
  deploy:
    replicas: 4
  environment:
    - API_WORKERS=4
```

### Vertical Scaling

```yaml
# Limites de ressources
api:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
```

### Async Processing

```python
# Traitement asynchrone pour l'API
@app.post("/analyze")
async def analyze_data(file: UploadFile):
    # Utilise asyncio pour ne pas bloquer
    result = await process_async(file)
```

---

##  Monitoring & Logging

### Logging Structuré

```python
logger.info(
    "Opération terminée",
    extra={
        'duration': elapsed,
        'rows': len(df),
        'status': 'success'
    }
)
```

### Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        'status': 'healthy',
        'redis': redis_connected(),
        'disk': disk_available()
    }
```

---

##  Documentation

### Docstrings (Google Style)

```python
def calculate_kpis(self, df: pd.DataFrame) -> Dict[str, float]:
    """
    Calcule les KPIs métier.
    
    Args:
        df: DataFrame de ventes avec colonnes 'prix' et 'quantite'
        
    Returns:
        Dict contenant les KPIs:
            - revenue_total: CA total
            - transaction_count: Nombre de transactions
            - average_basket: Panier moyen
            
    Example:
        >>> kpis = aggregator.calculate_kpis(df)
        >>> print(kpis['revenue_total'])
        125000.50
    """
```

---

##  Évolutions Futures

### Phase 2 (Court terme)

- [ ] Support PostgreSQL / MongoDB
- [ ] Authentification JWT
- [ ] Websockets pour streaming
- [ ] Celery pour tâches asynchrones

### Phase 3 (Moyen terme)

- [ ] Machine Learning (prédictions)
- [ ] Dashboard temps réel
- [ ] Multi-tenancy
- [ ] Internationalisation (i18n)

### Phase 4 (Long terme)

- [ ] Microservices architecture
- [ ] Kubernetes deployment
- [ ] Data Lake integration
- [ ] AI-powered insights




