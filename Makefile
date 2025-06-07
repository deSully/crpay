.PHONY: clean createsuperuser format lint check all

# Nettoyage des fichiers .pyc, __pycache__, etc.
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	echo "✅ Nettoyage terminé."

# Lint avec ruff
lint:
	ruff check .

# Formatage (imports, style, etc.) avec ruff
format:
	ruff format .
	ruff check --select I --fix  .

# Vérification complète
check: lint format

# Création d'un superutilisateur Django (saisie interactive)
createsuperuser:
	python manage.py createsuperuser

# Tout faire (utile pour CI ou en local)
all: clean check
