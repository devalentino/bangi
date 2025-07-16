include .env
export

pytest:
	echo "=== Running Pytest ==="
	pytest --envfile=.env ./tests

check-black:
	echo "=== Running Black Checker ==="
	black --check --diff -l 120 -S ./src ./tests

check-flake8:
	echo "=== Running Flake8 Checker ==="
	flake8 --ignore=E203,E711,E712,W503 --max-line-length=120 ./src ./tests

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
	pw_migrate migrate --name $(name) --database mysql://$(MYSQL_USERNAME)@$(MYSQL_HOST):$(MYSQL_PORT)/$(MYSQL_DB) --directory migrations

generate-migration:
	echo "=== Generating Migration ==="
	pw_migrate create  --auto  --auto-source src --directory migrations --database mysql://$(MYSQL_USERNAME)@$(MYSQL_HOST):$(MYSQL_PORT)/$(MYSQL_DB) $(name)
