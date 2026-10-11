"""Mostra o total e as últimas dez transações salvas, sem alterar o banco."""

import json
import sqlite3

from banco import CAMINHO_BANCO


def main():
    if not CAMINHO_BANCO.exists():
        print("O banco ainda não existe. Execute o consumidor primeiro.")
        return
    with sqlite3.connect(CAMINHO_BANCO.as_uri() + "?mode=ro", uri=True) as banco:
        total = banco.execute("SELECT COUNT(*) FROM transacoes").fetchone()[0]
        suspeitas = banco.execute(
            "SELECT COUNT(*) FROM transacoes WHERE alertas != '[]'"
        ).fetchone()[0]
        print(f"Transações salvas: {total} | Transações com alertas: {suspeitas}")
        colunas = {coluna[1] for coluna in banco.execute("PRAGMA table_info(transacoes)")}
        coluna_pais = "country" if "country" in colunas else "'BR'"
        linhas = banco.execute(f"""
            SELECT id, cliente_id, amount_centavos, cidade, data_hora, alertas,
                   {coluna_pais} AS country
            FROM transacoes ORDER BY instante DESC, rowid DESC LIMIT 10
        """).fetchall()
        for identificador, cliente, centavos, cidade, horario, alertas, pais in linhas:
            valor = f"{centavos // 100},{centavos % 100:02d}"
            regras = ", ".join(json.loads(alertas)) or "nenhum"
            print(f"{identificador} | {cliente} | R$ {valor} | {pais} | {cidade} | {horario} | {regras}")


if __name__ == "__main__":
    main()
