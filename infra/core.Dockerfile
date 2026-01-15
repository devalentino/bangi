FROM python:3.12 AS base

RUN mkdir /app
WORKDIR /app

COPY pyproject.toml /app
COPY requirements.txt /app
COPY migrations /app/migrations
COPY src /app/src

RUN pip install -r requirements.txt

CMD pw_migrate migrate --database mysql://$MARIADB_USER:$MARIADB_PASSWORD@$MARIADB_HOST:$MARIADB_PORT/$MARIADB_DATABASE \
    && gunicorn --bind 0.0.0.0:5000 src.api:app
