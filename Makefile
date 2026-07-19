# Makefile : des raccourcis pour lancer les taches courantes.
# Sur Windows, si "make" n'est pas installe, on peut copier-coller les commandes.

.PHONY: install test lint pipeline dashboard clean

# Installer les dependances
install:
	pip install -r requirements.txt

# Lancer toute la pipeline (scraping -> etl -> analyse -> alertes)
pipeline:
	python main.py

# Lancer le dashboard Streamlit
dashboard:
	streamlit run src/dashboard/app.py

# Lancer les tests avec la couverture
test:
	pytest --cov=src --cov-report=term-missing

# Generer le rapport Word
report:
	python docs/generate_report.py

# Nettoyer les fichiers temporaires
clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
