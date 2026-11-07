"""Plano de testes automatizado do QuadraFácil (CT01 a CT07).

Execute na raiz do projeto:  python -m unittest tests.test_sistema -v
"""
import os
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta

import db as banco
from app import create_app

AMANHA = (date.today() + timedelta(days=1)).isoformat()


class SistemaTestCase(unittest.TestCase):
    def setUp(self):
        self.arquivo = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.arquivo.close()
        banco.init_db(self.arquivo.name)
        con = sqlite3.connect(self.arquivo.name)
        con.execute("INSERT INTO cliente (nome, telefone) VALUES "
                    "('Carlos Eduardo Lima', '11900000001')")
        con.commit()
        con.close()
        self.cliente = create_app(self.arquivo.name).test_client()
        self.cliente.post("/login", data={"login": "atendente",
                                          "senha": "atendente123"})

    def tearDown(self):
        os.unlink(self.arquivo.name)

    def consultar(self, sql, params=()):
        con = sqlite3.connect(self.arquivo.name)
        resultado = con.execute(sql, params).fetchall()
        con.close()
        return resultado

    def reservar(self, inicio, fim, quadra="2", cliente="1"):
        return self.cliente.post("/reservas/nova", follow_redirects=True, data={
            "id_cliente": cliente, "id_quadra": quadra, "data": AMANHA,
            "hora_inicio": inicio, "hora_fim": fim})

    # -------------------------------------------- Funcionalidade 1: clientes
    def test_ct01_cadastro_cliente_dados_validos(self):
        """CT01 - Cadastro de cliente com dados válidos."""
        resp = self.cliente.post("/clientes", follow_redirects=True, data={
            "nome": "Mariana Alves Costa", "telefone": "(11) 90000-0002",
            "email": "mariana.costa@email.com"})
        html = resp.get_data(as_text=True)
        self.assertIn("cadastrado com sucesso", html)
        self.assertIn("Mariana Alves Costa", html)
        self.assertEqual(len(self.consultar("SELECT * FROM cliente")), 2)

    def test_ct02_cadastro_cliente_sem_nome(self):
        """CT02 - Cadastro de cliente sem preencher o nome."""
        resp = self.cliente.post("/clientes", data={
            "nome": "", "telefone": "11900000009", "email": ""})
        self.assertIn("nome do cliente é obrigatório", resp.get_data(as_text=True))
        self.assertEqual(len(self.consultar("SELECT * FROM cliente")), 1)

    def test_ct03_cadastro_cliente_telefone_invalido(self):
        """CT03 - Cadastro de cliente com telefone inválido."""
        resp = self.cliente.post("/clientes", data={
            "nome": "Rafael Souza Pereira", "telefone": "12345", "email": ""})
        self.assertIn("telefone válido", resp.get_data(as_text=True))
        self.assertEqual(len(self.consultar("SELECT * FROM cliente")), 1)

    # --------------------------------------------- Funcionalidade 2: reservas
    def test_ct04_reserva_valida(self):
        """CT04 - Reserva de quadra em horário livre."""
        html = self.reservar("19:00", "21:00").get_data(as_text=True)
        self.assertIn("Reserva confirmada com sucesso", html)
        linhas = self.consultar("SELECT valor_total, status FROM reserva")
        self.assertEqual(linhas, [(180.0, "CONFIRMADA")])   # 2 h x R$ 90,00

    def test_ct05_reserva_horario_ocupado(self):
        """CT05 - Reserva em horário já ocupado (sobreposição)."""
        self.reservar("19:00", "21:00")
        html = self.reservar("20:00", "22:00").get_data(as_text=True)
        self.assertIn("Horário indisponível", html)
        self.assertEqual(len(self.consultar("SELECT * FROM reserva")), 1)

    def test_ct06_reserva_hora_final_invalida(self):
        """CT06 - Reserva com hora final menor que a inicial."""
        html = self.reservar("21:00", "19:00").get_data(as_text=True)
        self.assertIn("horário final deve ser maior", html)
        self.assertEqual(len(self.consultar("SELECT * FROM reserva")), 0)

    # ------------------------------------------------------------- segurança
    def test_ct07_acesso_sem_login(self):
        """CT07 - Acesso a página protegida sem autenticação."""
        anonimo = create_app(self.arquivo.name).test_client()
        resp = anonimo.get("/reservas")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])


if __name__ == "__main__":
    unittest.main()
