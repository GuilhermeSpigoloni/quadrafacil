"""QuadraFácil - Sistema de reserva de quadras esportivas.

Projeto Integrado Interdisciplinar - Análise e Desenvolvimento de Sistemas
Autor: Guilherme Spigoloni Godinho
"""
import os
from datetime import date
from functools import wraps

from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for)
from werkzeug.security import check_password_hash

import db as banco
import regras


def create_app(caminho_banco=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("QF_SECRET", "troque-esta-chave")
    app.config["DATABASE"] = caminho_banco or os.path.join(
        banco.BASE_DIR, "quadrafacil.db")
    app.teardown_appcontext(banco.close_db)

    # ---------------------------------------------------- filtros de formato
    @app.template_filter("brl")
    def brl(valor):
        texto = f"{valor or 0:,.2f}".replace(",", "X").replace(".", ",")
        return "R$ " + texto.replace("X", ".")

    @app.template_filter("data_br")
    def data_br(texto):
        ano, mes, dia = texto.split("-")
        return f"{dia}/{mes}/{ano}"

    @app.template_filter("fone")
    def fone(numero):
        if len(numero) == 11:
            return f"({numero[:2]}) {numero[2:7]}-{numero[7:]}"
        return f"({numero[:2]}) {numero[2:6]}-{numero[6:]}"

    # ------------------------------------------------------- controle de acesso
    def login_required(rota):
        @wraps(rota)
        def protegida(*args, **kwargs):
            if "id_usuario" not in session:
                flash("Faça login para acessar o sistema.", "erro")
                return redirect(url_for("login"))
            return rota(*args, **kwargs)
        return protegida

    # ------------------------------------------------------------------ login
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            usuario = banco.get_db().execute(
                "SELECT * FROM usuario WHERE login = ?",
                (request.form.get("login", "").strip(),),
            ).fetchone()
            senha = request.form.get("senha", "")
            if usuario and check_password_hash(usuario["senha_hash"], senha):
                session.clear()
                session["id_usuario"] = usuario["id_usuario"]
                session["nome_usuario"] = usuario["nome"]
                session["perfil"] = usuario["perfil"]
                return redirect(url_for("reservas"))
            flash("Usuário ou senha inválidos.", "erro")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/")
    def inicio():
        return redirect(url_for("reservas"))

    # ------------------------------------- FUNCIONALIDADE 1: cadastro de cliente
    @app.route("/clientes", methods=["GET", "POST"])
    @login_required
    def clientes():
        db = banco.get_db()
        formulario = {}
        if request.method == "POST":
            dados, erros = regras.validar_cliente(request.form)
            if erros:
                for erro in erros:
                    flash(erro, "erro")
                formulario = request.form          # mantém o que foi digitado
            else:
                db.execute(
                    "INSERT INTO cliente (nome, telefone, email) VALUES (?, ?, ?)",
                    (dados["nome"], dados["telefone"], dados["email"]),
                )
                db.commit()
                flash(f"Cliente {dados['nome']} cadastrado com sucesso!", "sucesso")
                return redirect(url_for("clientes"))
        lista = db.execute(
            "SELECT * FROM cliente ORDER BY nome COLLATE NOCASE").fetchall()
        return render_template("clientes.html", clientes=lista, f=formulario)

    # ----------------------------------------- FUNCIONALIDADE 2: reservar quadra
    @app.route("/reservas/nova", methods=["GET", "POST"])
    @login_required
    def nova_reserva():
        db = banco.get_db()
        formulario = {}
        if request.method == "POST":
            dados, erros = regras.validar_reserva(request.form, db)
            if not erros:
                # BEGIN IMMEDIATE trava a escrita: evita duas reservas simultâneas
                db.execute("BEGIN IMMEDIATE")
                if regras.existe_conflito(db, dados["id_quadra"], dados["data"],
                                          dados["hora_inicio"], dados["hora_fim"]):
                    db.rollback()
                    erros.append("Horário indisponível: já existe reserva "
                                 "para esta quadra neste período.")
                else:
                    valor = regras.calcular_valor(
                        dados["quadra"]["valor_hora"],
                        dados["hora_inicio"], dados["hora_fim"])
                    db.execute(
                        "INSERT INTO reserva (id_cliente, id_quadra, id_usuario, "
                        "data, hora_inicio, hora_fim, valor_total) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (dados["id_cliente"], dados["id_quadra"],
                         session["id_usuario"], dados["data"],
                         dados["hora_inicio"], dados["hora_fim"], valor),
                    )
                    db.commit()
                    flash("Reserva confirmada com sucesso!", "sucesso")
                    return redirect(url_for("reservas", data=dados["data"]))
            for erro in erros:
                flash(erro, "erro")
            formulario = request.form
        return render_template(
            "reserva_nova.html", f=formulario,
            clientes=db.execute(
                "SELECT id_cliente, nome FROM cliente "
                "ORDER BY nome COLLATE NOCASE").fetchall(),
            quadras=db.execute(
                "SELECT * FROM quadra WHERE ativa = 1 ORDER BY nome").fetchall(),
            hoje=date.today().isoformat())

    # ------------------------------------------------- consulta: reservas do dia
    @app.route("/reservas")
    @login_required
    def reservas():
        dia = request.args.get("data") or date.today().isoformat()
        lista = banco.get_db().execute(
            "SELECT r.id_reserva, r.hora_inicio, r.hora_fim, r.valor_total, "
            "r.status, c.nome AS cliente, c.telefone, q.nome AS quadra "
            "FROM reserva r "
            "JOIN cliente c ON c.id_cliente = r.id_cliente "
            "JOIN quadra  q ON q.id_quadra  = r.id_quadra "
            "WHERE r.data = ? ORDER BY r.hora_inicio, q.nome", (dia,)
        ).fetchall()
        return render_template("reservas.html", reservas=lista, dia=dia)

    @app.route("/reservas/<int:id_reserva>/cancelar", methods=["POST"])
    @login_required
    def cancelar_reserva(id_reserva):
        db = banco.get_db()
        reserva = db.execute(
            "SELECT data FROM reserva WHERE id_reserva = ?", (id_reserva,)
        ).fetchone()
        if reserva is None:
            flash("Reserva não encontrada.", "erro")
            return redirect(url_for("reservas"))
        db.execute("UPDATE reserva SET status = 'CANCELADA' "
                   "WHERE id_reserva = ?", (id_reserva,))
        db.commit()
        flash("Reserva cancelada. O horário foi liberado.", "sucesso")
        return redirect(url_for("reservas", data=reserva["data"]))

    # ------------------------------------------------------ relatório (gerente)
    @app.route("/relatorio")
    @login_required
    def relatorio():
        if session.get("perfil") != "GERENTE":
            flash("Acesso restrito ao perfil Gerente.", "erro")
            return redirect(url_for("reservas"))
        hoje = date.today()
        inicio = request.args.get("inicio") or hoje.replace(day=1).isoformat()
        fim = request.args.get("fim") or hoje.isoformat()
        linhas = banco.get_db().execute(
            "SELECT q.nome AS quadra, "
            "SUM(CASE WHEN r.status = 'CONFIRMADA' THEN 1 ELSE 0 END) AS confirmadas, "
            "SUM(CASE WHEN r.status = 'CANCELADA'  THEN 1 ELSE 0 END) AS canceladas, "
            "COALESCE(SUM(CASE WHEN r.status = 'CONFIRMADA' "
            "THEN r.valor_total END), 0) AS faturamento "
            "FROM quadra q LEFT JOIN reserva r "
            "ON r.id_quadra = q.id_quadra AND r.data BETWEEN ? AND ? "
            "GROUP BY q.id_quadra ORDER BY q.nome", (inicio, fim)
        ).fetchall()
        total = sum(l["faturamento"] for l in linhas)
        return render_template("relatorio.html", linhas=linhas, total=total,
                               inicio=inicio, fim=fim)

    return app


if __name__ == "__main__":
    caminho = os.path.join(banco.BASE_DIR, "quadrafacil.db")
    if not os.path.exists(caminho):
        banco.init_db(caminho)
    create_app(caminho).run(debug=True)
