#  Quick Start - Démarrage Rapide en 5 Minutes

Guide pour démarrer **immédiatement** avec la plateforme d'analyse de données.

---

##  Installation Express (3 commandes)

```bash
# 1. Cloner et entrer
git clone https://github.com/JbeySaros/projet_analyse
cd projet_analyse

# 2. Installation automatique
make full-install

# 3. Vérifier
make check-env
```

 **Done** La plateforme est prête à analyser des données.

---

##  Première Analyse (2 minutes)

### Option 1 : Avec vos données

1. **Placez votre CSV dans `data/`**
```bash
cp /path/to/your/ventes.csv data/
```

2. **Lancez l'analyse**
```bash
python main.py data/ventes.csv
```

3. **Consultez les résultats**
```bash
open outputs/rapport_analyse.html
```

### Option 2 : Avec des données de test

1. **Créez un fichier test**
```bash
cat > data/test.csv << EOF
date,produit,categorie,prix,quantite,ville,source
2025-01-01,Stylo,Fournitures,1.5,10,Paris,web
2025-01-02,Cahier,Fournitures,3.0,5,Lyon,magasin
2025-01-03,Calculatrice,Electronique,15.0,2,Marseille,web
EOF
```

2. **Analysez**
```bash
python main.py data/test.csv
```

---

##  Démarrer l'API (1 minute)

```bash
# Lancer l'API
make run-api

# Dans un autre terminal, tester
curl http://localhost:8000/health
```

 **Documentation interactive** : http://localhost:8000/api/docs

---

##  Version Docker (30 secondes)

```bash
# Tout démarrer (API + Redis)
make docker-up

# Vérifier
curl http://localhost:8000/health
```

---

##  Exemples de Commandes

### CLI Pipeline

```bash
# Analyse basique
python main.py data/ventes.csv

# Sans nettoyage
python main.py data/ventes.csv --skip-cleaning

# Sans rapport (plus rapide)
python main.py data/ventes.csv --no-report

# Répertoire personnalisé
python main.py data/ventes.csv -o resultats/janvier
```

### API REST

```bash
# Upload fichier
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@data/ventes.csv"

# Analyse complète
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@data/ventes.csv" \
  -F "clean=true"

# Générer rapport HTML
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -F "file=@data/ventes.csv" \
  -F "format=html" \
  --output rapport.html
```

### Python Programmatique

```python
from data_loader import CSVLoader
from data_processor import DataAggregator

# Charger
loader = CSVLoader()
df = loader.load("data/ventes.csv")

# Analyser
aggregator = DataAggregator()
kpis = aggregator.calculate_kpis(df)

print(f"CA Total: {kpis['revenue_total']:.2f}€")
print(f"Transactions: {kpis['transaction_count']}")
```

---

##  Tests (30 secondes)

```bash
# Tous les tests
make test

# Avec couverture
make coverage

# Ouvrir rapport de couverture
open htmlcov/index.html
```

---

##  Configuration Rapide

### Personnaliser les Paramètres

```bash
# Copier le template
cp .env.example .env

# Éditer (nano, vim, ou éditeur)
nano .env
```

**Paramètres clés** :
```bash
# Environnement
ENVIRONMENT=development
DEBUG=True

# Logs
LOG_LEVEL=INFO

# Cache Redis
REDIS_HOST=localhost
CACHE_ENABLED=True

# Limites
MAX_FILE_SIZE=104857600  # 100 MB
```

---

##  Structure Minimale Nécessaire

```
projet_analyse/
├── data/              # Vos fichiers CSV ici
│   └── ventes.csv
├── config.py
├── main.py
└── requirements.txt
```

Tout le reste est créé automatiquement

---

## Troubleshooting

### Problème : Module non trouvé

```bash
# Vérifier environnement virtuel
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Réinstaller
pip install -r requirements.txt
```

### Problème : Redis non disponible

```bash
# L'API fonctionne sans Redis (cache désactivé)
# Pour activer Redis :

# Option 1: Docker
make docker-up

# Option 2: Local
redis-server --daemonize yes
```

### Problème : Port 8000 occupé

```bash
# Changer le port
uvicorn api.main:app --port 8001
```

### Problème : Fichier trop gros

```python
# Utiliser le chunking
loader = CSVLoader(chunk_size=5000)
df = loader.load("big_file.csv", use_chunks=True)
```

---

##  Prochaines Étapes

Maintenant que vous êtes lancé :

1.  **Lire la doc complète** : [README.md](README.md)
2.  **Guide d'utilisation** : [USAGE_GUIDE.md](USAGE_GUIDE.md)
3. **Comprendre l'architecture** : [ARCHITECTURE.md](ARCHITECTURE.md)
4.  **Synthèse détaillée** : [SYNTHESE_PROJET.md](SYNTHESE_PROJET.md)

---

## 💡 Commandes Utiles (Mémo)

```bash
# Installation & Setup
make install          # Installer dépendances
make setup           # Setup initial complet
make full-install    # Installation + setup

# Exécution
make run-pipeline    # CLI pipeline
make run-api         # API en dev mode
make run-api-prod    # API en production

# Docker
make docker-build    # Build images
make docker-up       # Démarrer services
make docker-down     # Arrêter services
make docker-logs     # Voir les logs

# Tests & Qualité
make test            # Lancer tests
make test-unit       # Tests unitaires seulement
make coverage        # Tests avec couverture
make lint            # Linter le code
make format          # Formatter avec Black
make quality         # Lint + format + type-check

# Utilitaires
make clean           # Nettoyer fichiers temp
make check-env       # Vérifier configuration
make version         # Afficher version
```

---

##  Résultats Attendus

Après une analyse, vous obtiendrez :

```
outputs/
├── rapport_analyse.html          # Rapport interactif complet
├── resultats_analyse.xlsx        # Export Excel multi-feuilles
└── charts/                       # Graphiques HTML
    ├── ventes_categorie.html
    ├── repartition_villes.html
    ├── evolution_ca.html
    ├── top_produits.html
    └── correlation_matrix.html
```

---

##  C'est Parti !


