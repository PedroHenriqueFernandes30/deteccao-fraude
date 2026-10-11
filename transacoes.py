"""Gera transações simuladas no formato definido pelo professor."""

import json
import random
import time
from datetime import datetime
from uuid import uuid4

from modelo import FUSO_HORARIO, id_cliente_legado


CLIENTES = [id_cliente_legado(f"cliente-{numero:02d}") for numero in range(1, 6)]
CIDADES = ["São Paulo", "Recife", "Curitiba", "Salvador"]


def gerar_transacao():
    return {
        "id_transacao": str(uuid4()),
        "id_cliente": random.choice(CLIENTES),
        "valor": random.randint(100, 1500000) / 100,
        "country": "BR",
        "city": random.choice(CIDADES),
        "hora": datetime.now(FUSO_HORARIO).replace(tzinfo=None).isoformat(timespec="seconds"),
    }


def main():
    print("Gerando transações a cada 3 segundos. Ctrl+C para encerrar.")
    try:
        while True:
            print(json.dumps(gerar_transacao(), ensure_ascii=False), flush=True)
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nGerador encerrado.")


if __name__ == "__main__":
    main()
