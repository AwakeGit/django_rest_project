# Makefile

lint:
	poetry run black .
	poetry run isort .
	poetry run flake8

test:
	poetry run pytest

coverage:
	poetry run coverage run -m pytest
	poetry run coverage report
