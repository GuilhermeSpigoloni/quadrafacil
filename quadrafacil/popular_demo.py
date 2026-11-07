"""Popula o banco com dados fictícios para demonstração (opcional)."""
import os
import sqlite3
from datetime import date

import db as banco

caminho = os.path.join(banco.BASE_DIR, "quadrafacil.db")
banco.init_db(caminho)
con = sqlite3.connect(caminho)
clientes = [
    ("Carlos Eduardo Lima", "11900000001", "carlos.lima@email.com"),
    ("Mariana Alves Costa", "11900000002", "mariana.costa@email.com"),
    ("Rafael Souza Pereira", "11900000003", None),
    ("Juliana Martins", "11900000004", "ju.martins@email.com"),
]
con.executemany("INSERT INTO cliente (nome, telefone, email) VALUES (?, ?, ?)", clientes)
hoje = date.today().isoformat()
reservas = [  # cliente, quadra, usuário, início, fim, valor
    (1, 1, 1, "18:00", "19:00", 120.0),
    (2, 2, 1, "19:00", "21:00", 180.0),
    (3, 3, 1, "20:00", "21:00", 60.0),
]
for cli, qua, usu, ini, fim, valor in reservas:
    con.execute(
        "INSERT INTO reserva (id_cliente, id_quadra, id_usuario, data, "
        "hora_inicio, hora_fim, valor_total) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (cli, qua, usu, hoje, ini, fim, valor))
con.commit()
con.close()
print("Banco populado com dados de demonstração.")
