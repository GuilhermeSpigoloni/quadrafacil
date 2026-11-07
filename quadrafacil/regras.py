"""Regras de negócio e validações do QuadraFácil."""
import re
from datetime import date, datetime


def somente_digitos(texto):
    """Remove tudo que não for número (ex.: '(11) 98888-7777' -> '11988887777')."""
    return re.sub(r"\D", "", texto or "")


# ---------------------------------------------------------------- Clientes
def validar_cliente(form):
    """Valida o formulário de cadastro de cliente.

    Retorna (dados, erros). Se 'erros' estiver vazia, os dados podem ser gravados.
    """
    nome = " ".join((form.get("nome") or "").split())
    telefone = somente_digitos(form.get("telefone"))
    email = (form.get("email") or "").strip().lower()
    erros = []

    if len(nome) < 3:
        erros.append("O nome do cliente é obrigatório (mínimo de 3 caracteres).")
    if len(telefone) not in (10, 11):
        erros.append("Informe um telefone válido com DDD (10 ou 11 dígitos).")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("O e-mail informado é inválido.")

    return {"nome": nome, "telefone": telefone, "email": email or None}, erros


# ---------------------------------------------------------------- Reservas
def calcular_valor(valor_hora, hora_inicio, hora_fim):
    """Valor total = valor da hora x duração (em horas) da reserva."""
    ini = datetime.strptime(hora_inicio, "%H:%M")
    fim = datetime.strptime(hora_fim, "%H:%M")
    horas = (fim - ini).total_seconds() / 3600
    return round(valor_hora * horas, 2)


def existe_conflito(db, id_quadra, data, hora_inicio, hora_fim):
    """Há reserva CONFIRMADA na mesma quadra e data que se sobreponha ao intervalo?

    Dois intervalos se sobrepõem quando: inicio_existente < fim_novo
    E fim_existente > inicio_novo.
    """
    linha = db.execute(
        "SELECT 1 FROM reserva "
        "WHERE id_quadra = ? AND data = ? AND status = 'CONFIRMADA' "
        "AND hora_inicio < ? AND hora_fim > ? LIMIT 1",
        (id_quadra, data, hora_fim, hora_inicio),
    ).fetchone()
    return linha is not None


def validar_reserva(form, db, hoje=None):
    """Valida o formulário de reserva (sem verificar conflito de horário).

    Retorna (dados, erros).
    """
    hoje = hoje or date.today()
    erros = []
    dados = {
        "id_cliente": form.get("id_cliente", ""),
        "id_quadra": form.get("id_quadra", ""),
        "data": form.get("data", ""),
        "hora_inicio": form.get("hora_inicio", ""),
        "hora_fim": form.get("hora_fim", ""),
    }

    cliente = quadra = None
    if dados["id_cliente"].isdigit():
        cliente = db.execute(
            "SELECT * FROM cliente WHERE id_cliente = ?", (dados["id_cliente"],)
        ).fetchone()
    if cliente is None:
        erros.append("Selecione um cliente cadastrado.")

    if dados["id_quadra"].isdigit():
        quadra = db.execute(
            "SELECT * FROM quadra WHERE id_quadra = ? AND ativa = 1",
            (dados["id_quadra"],),
        ).fetchone()
    if quadra is None:
        erros.append("Selecione uma quadra válida.")

    try:
        dia = datetime.strptime(dados["data"], "%Y-%m-%d").date()
        if dia < hoje:
            erros.append("Não é possível reservar em uma data passada.")
    except ValueError:
        erros.append("Informe uma data válida.")

    try:
        ini = datetime.strptime(dados["hora_inicio"], "%H:%M")
        fim = datetime.strptime(dados["hora_fim"], "%H:%M")
        if fim <= ini:
            erros.append("O horário final deve ser maior que o horário inicial.")
    except ValueError:
        erros.append("Informe horários válidos (início e fim).")

    dados["cliente"], dados["quadra"] = cliente, quadra
    return dados, erros
