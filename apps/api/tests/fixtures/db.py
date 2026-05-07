import json
from uuid import UUID

import pytest
from pymysql import cursors


def cast_db_value(value):
    if isinstance(value, UUID):
        return value.bytes
    if isinstance(value, (list, dict)):
        return json.dumps(value, default=str)
    return value


def cast_read_value(value):
    if isinstance(value, (bytes, bytearray)) and len(value) == 16:
        return UUID(bytes=bytes(value))
    return value


@pytest.fixture
def write_to_db(mysql):
    def _write_to_db(table, payload, returning=True):
        column_names = payload.keys()
        value_placeholders = [f"%({key})s" for key in payload.keys()]

        query = f'INSERT INTO {table} ({", ".join(column_names)}) VALUES ({", ".join(value_placeholders)})'
        values = {k: cast_db_value(v) for k, v in payload.items()}

        with mysql.cursor(cursors.DictCursor) as cur:
            cur.execute(query, values)

            if not returning:
                mysql.commit()
                return

            id_ = cur.lastrowid
            cur.execute(f'SELECT * FROM {table} WHERE id = %(id)s', {"id": id_})
            row = cur.fetchone()
            mysql.commit()

            return {key: cast_read_value(value) for key, value in row.items()}

    return _write_to_db


@pytest.fixture
def read_from_db(mysql):
    def _read_from_db(table, columns=None, filters=None, fetchall=False):
        column_names = ", ".join(columns) if columns else "*"
        query = f'SELECT {column_names} FROM {table} '

        if filters is not None:
            column_names = " AND ".join(f"{column_name}=%({column_name})s" for column_name, value in filters.items())
            query += f"WHERE {column_names}"
            filters = {k: cast_db_value(v) for k, v in filters.items()}

        with mysql.cursor(cursors.DictCursor) as cur:
            cur.execute(query, filters)
            if fetchall:
                result = [{key: cast_read_value(value) for key, value in row.items()} for row in cur.fetchall()]
            else:
                row = cur.fetchone()
                result = {key: cast_read_value(value) for key, value in row.items()} if row else None

            mysql.commit()
            return result

    return _read_from_db
