from decimal import Decimal
import psycopg
from psycopg.rows import dict_row

from config import DATABASE_URL


def _float_dict_row(cursor):
    """
    Like psycopg's built-in dict_row, but also converts Postgres NUMERIC
    columns (which arrive as Python Decimal) into plain floats. Without
    this, returning a row straight from the database in a FastAPI response
    fails with "Object of type Decimal is not JSON serializable".
    """
    make_row = dict_row(cursor)

    def row_maker(values):
        row = make_row(values)
        return {k: (float(v) if isinstance(v, Decimal) else v) for k, v in row.items()}

    return row_maker


def get_db():
    """FastAPI dependency: `db = Depends(get_db)` in a route function."""
    conn = psycopg.connect(DATABASE_URL, row_factory=_float_dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
