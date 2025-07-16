import pymysql.cursors
import pytest


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
