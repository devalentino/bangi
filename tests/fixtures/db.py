import json

import pymysql.cursors
import pytest


@pytest.fixture
def write_to_db(mysql):
    def _write_to_db(table, payload, returning=True):
        column_names = payload.keys()
        value_placeholders = [f"%({key})s" for key in payload.keys()]

        query = f'INSERT INTO {table} ({", ".join(column_names)}) VALUES ({", ".join(value_placeholders)})'
        values = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in payload.items()}

        cur = mysql.cursor(pymysql.cursors.DictCursor)
        cur.execute(query, values)

        if not returning:
            mysql.commit()
            return

        id_ = cur.lastrowid
        cur.execute(f'SELECT * FROM {table} WHERE id = %(id)s', {"id": id_})
        row = cur.fetchone()
        mysql.commit()

        return row

    return _write_to_db


@pytest.fixture
def read_from_db(mysql):
    def _read_from_db(table, columns=None, filters=None, fetchone=True):
        column_names = ", ".join(columns) if columns else "*"
        query = f'SELECT {column_names} FROM {table} '

        if filters is not None:
            column_names = ", ".join(f"{column_name}=%({column_name})s" for column_name, value in filters.items())
            query += f"WHERE {column_names}"

        cur = mysql.cursor(pymysql.cursors.DictCursor)
        cur.execute(query, filters)
        if fetchone:
            return cur.fetchone()
        else:
            return cur.fetchall()

    return _read_from_db
