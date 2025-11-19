.PHONY: help install test run-api docker-up clean

help:
	@echo "Commandes disponibles:"
	@echo "  make install       - Installer les dépendances"
	@echo "  make test          - Lancer les tests"
	@echo "  make run-api       - Démarrer l'API"
	@echo "  make docker-up     - Démarrer avec Docker"
	@echo "  make clean         - Nettoyer les fichiers temporaires"

install:
	pip install -r requirements.txt

test:
	pytest

run-api:
	python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

run-pipeline:
	python main.py data/vente_2025.csv

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .pytest_cache/ .coverage
