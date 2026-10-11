"""Salva transações e usa o histórico do cliente para detectar suspeitas."""

import json
import sqlite3
from datetime import datetime
from decimal import Decimal
from pathlib import Path


CAMINHO_BANCO = Path(__file__).resolve().parent / "transacoes.db"


def abrir_banco(caminho=CAMINHO_BANCO):
    banco = sqlite3.connect(caminho)
    banco.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id TEXT PRIMARY KEY,
            cliente_id TEXT NOT NULL,
            amount_centavos INTEGER NOT NULL,
            cidade TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            instante REAL NOT NULL,
            alertas TEXT NOT NULL,
            dados_originais TEXT NOT NULL
        )
    """)
    banco.execute("""
        CREATE INDEX IF NOT EXISTS historico_cliente
        ON transacoes (cliente_id, instante)
    """)
    banco.commit()
    return banco


def salvar_transacao(banco, transacao):
    """Retorna (alertas, nova). Reentregas do mesmo id não duplicam a compra."""
    horario = datetime.fromisoformat(transacao["data_hora"])
    if horario.tzinfo is None:
        raise ValueError("data_hora precisa informar o fuso horário")
    instante = horario.timestamp()
    valor = Decimal(str(transacao["amount"]))
    centavos = valor * 100
    if not valor.is_finite() or valor < 0 or centavos != centavos.to_integral_value():
        raise ValueError("amount precisa ser positivo ou zero, com até duas casas decimais")

    with banco:
        existente = banco.execute(
            "SELECT alertas FROM transacoes WHERE id = ?", (transacao["id"],)
        ).fetchone()
        if existente:
            return json.loads(existente[0]), False

        historico = banco.execute("""
            SELECT instante, cidade FROM transacoes
            WHERE cliente_id = ? AND instante >= ? AND instante <= ?
        """, (transacao["cliente_id"], instante - 600, instante)).fetchall()

        alertas = []
        if valor >= 10000:
            alertas.append("ALTO_VALOR")

        # A transação atual também conta: três anteriores + esta = quatro.
        recentes = sum(1 for anterior, _ in historico if instante - anterior < 60)
        if recentes >= 3:
            alertas.append("TEMPO_60s")

        if any(cidade != transacao["cidade"] for _, cidade in historico):
            alertas.append("GEO_10m")

        banco.execute("""
            INSERT INTO transacoes
            (id, cliente_id, amount_centavos, cidade, data_hora, instante,
             alertas, dados_originais)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transacao["id"], transacao["cliente_id"], int(centavos),
            transacao["cidade"], transacao["data_hora"], instante,
            json.dumps(alertas), json.dumps(transacao, ensure_ascii=False),
        ))
    return alertas, True
