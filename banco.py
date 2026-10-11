"""Salva transações e usa o histórico do cliente para detectar suspeitas."""

import json
import sqlite3
from decimal import Decimal
from pathlib import Path

from modelo import id_cliente_legado, instante_transacao, normalizar_transacao


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
            country TEXT NOT NULL DEFAULT 'BR',
            instante REAL NOT NULL,
            alertas TEXT NOT NULL,
            dados_originais TEXT NOT NULL
        )
    """)
    colunas = {coluna[1] for coluna in banco.execute("PRAGMA table_info(transacoes)")}
    if "country" not in colunas:
        # O primeiro produtor usava apenas cidades brasileiras.
        with banco:
            banco.execute("ALTER TABLE transacoes ADD COLUMN country TEXT NOT NULL DEFAULT 'BR'")
            for numero in range(1, 6):
                nome = f"cliente-{numero:02d}"
                banco.execute("UPDATE transacoes SET cliente_id = ? WHERE cliente_id = ?",
                              (id_cliente_legado(nome), nome))
    banco.execute("""
        CREATE INDEX IF NOT EXISTS historico_cliente
        ON transacoes (cliente_id, instante)
    """)
    banco.commit()
    return banco


def salvar_transacao(banco, transacao):
    """Retorna (alertas, nova). Reentregas do mesmo id não duplicam a compra."""
    original = transacao
    transacao = normalizar_transacao(original)
    instante = instante_transacao(transacao["hora"])
    valor = Decimal(str(transacao["valor"]))
    if not valor.is_finite() or valor < 0:
        raise ValueError("valor precisa ser finito e positivo ou zero")
    centavos = valor * 100
    if centavos != centavos.to_integral_value():
        raise ValueError("valor precisa ter até duas casas decimais")

    with banco:
        existente = banco.execute(
            "SELECT alertas FROM transacoes WHERE id = ?", (transacao["id_transacao"],)
        ).fetchone()
        if existente:
            return json.loads(existente[0]), False

        historico = banco.execute("""
            SELECT instante, cidade FROM transacoes
            WHERE cliente_id = ? AND instante >= ? AND instante <= ?
        """, (transacao["id_cliente"], instante - 600, instante)).fetchall()

        alertas = []
        if valor >= 10000:
            alertas.append("ALTO_VALOR")

        # A transação atual também conta: três anteriores + esta = quatro.
        recentes = sum(1 for anterior, _ in historico if instante - anterior < 60)
        if recentes >= 3:
            alertas.append("TEMPO_60s")

        if any(cidade != transacao["city"] for _, cidade in historico):
            alertas.append("GEO_10m")

        banco.execute("""
            INSERT INTO transacoes
            (id, cliente_id, amount_centavos, cidade, data_hora, instante,
             alertas, dados_originais, country)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transacao["id_transacao"], transacao["id_cliente"], int(centavos),
            transacao["city"], transacao["hora"], instante,
            json.dumps(alertas), json.dumps(original, ensure_ascii=False), transacao["country"],
        ))
    return alertas, True
