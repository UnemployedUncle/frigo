from contextlib import contextmanager

from psycopg import connect
from psycopg.rows import dict_row

from app.config import settings


@contextmanager
def get_connection():
    conn = connect(settings.database_url, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()
