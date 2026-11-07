# QuadraFácil — Sistema de Reserva de Quadras Esportivas

Projeto Integrado Interdisciplinar — Análise e Desenvolvimento de Sistemas (Anhanguera)
Autor: Guilherme Spigoloni Godinho

Protótipo funcional de um sistema web para controle de reservas de quadras esportivas
de uma arena de bairro. Tecnologias: Python 3, Flask e SQLite.

## Funcionalidades
- Login com perfis Atendente e Gerente (senha armazenada em hash)
- **Funcionalidade 1:** cadastro de clientes (grava no banco)
- **Funcionalidade 2:** reserva de quadras (lê clientes/quadras do banco, impede conflito de horário e grava a reserva)
- Consulta das reservas do dia, cancelamento de reservas e relatório de faturamento (Gerente)

## Como executar
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python popular_demo.py           # opcional: dados fictícios de demonstração
python app.py                    # acesse http://127.0.0.1:5000
```
Usuários iniciais: `atendente` / `atendente123` e `gerente` / `gerente123`.

## Testes
```bash
python -m unittest tests.test_sistema -v
```
