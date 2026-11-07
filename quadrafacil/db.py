"""Acesso ao banco de dados SQLite do QuadraFácil."""
import os
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_db():
    """Abre (uma vez por requisição) a conexão com o banco."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")  # integridade referencial
    return g.db


def close_db(erro=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(caminho):
    """Cria as tabelas (schema.sql) e os usuários iniciais."""
    con = sqlite3.connect(caminho)
    with open(os.path.join(BASE_DIR, "schema.sql"), encoding="utf-8") as arq:
        con.executescript(arq.read())
    usuarios = [
        ("Atendente da Arena", "atendente", "atendente123", "ATENDENTE"),
        ("Gerente da Arena", "gerente", "gerente123", "GERENTE"),
    ]
    for nome, login, senha, perfil in usuarios:
        con.execute(
            "INSERT OR IGNORE INTO usuario (nome, login, senha_hash, perfil) "
            "VALUES (?, ?, ?, ?)",
            (nome, login, generate_password_hash(senha), perfil),
        )
    con.commit()
    con.close()
