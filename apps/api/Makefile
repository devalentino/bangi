include .env
export

pytest:
	echo "=== Running Pytest ==="
	pytest -v --envfile=.env ./tests/integration

check-black:
	echo "=== Running Black Checker ==="
	black --check --diff -l 120 -S ./src ./tests

check-flake8:
	echo "=== Running Flake8 Checker ==="
	flake8 --ignore=E203,E711,E712,E731,W503 --max-line-length=120 ./src ./tests

check-isort:
	echo "=== Running Isort Checker ==="
	isort -l 120 --profile black ./src ./tests -c


test: check-black check-isort check-flake8 pytest

run-black:
	echo "=== Running Black ==="
	black -l 120 -S ./src ./tests

run-isort:
	echo "=== Running Isort ==="
	isort -l 120 --profile black ./src ./tests

lint: run-isort run-black check-flake8


# DB migrations
migrate:
	echo "=== Running Migrations ==="
	pw_migrate migrate --database "mysql://$(MARIADB_USER):$(MARIADB_PASSWORD)@$(MARIADB_HOST):$(MARIADB_PORT)/$(MARIADB_DATABASE)" --directory migrations

generate-migration:
	echo "=== Generating Migration ==="
	pw_migrate create  --auto  --auto-source src --directory migrations --database "mysql://$(MARIADB_USER):$(MARIADB_PASSWORD)@$(MARIADB_HOST):$(MARIADB_PORT)/$(MARIADB_DATABASE)" $(name)
