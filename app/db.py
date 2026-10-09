import os

import pymysql
from pymysql.cursors import DictCursor
from flask import g


def get_db():
    if "db" not in g:
        g.db = pymysql.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            port=int(os.environ.get("DB_PORT", 3307)),
            user=os.environ.get("DB_USER", "miskylac_user"),
            password=os.environ.get("DB_PASSWORD", "miskylac123"),
            database=os.environ.get("DB_NAME", "miskylac"),
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
        )
    return g.db


def close_db(_exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, params=()):
    """SELECT: devuelve una lista de diccionarios."""
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def init_db():
    get_db()  # Las tablas las crea Docker (01_schema.sql)


def init_app(app):
    app.teardown_appcontext(close_db)