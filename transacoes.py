"""Primeira etapa: gerar transações simuladas para depois enviar ao Kafka."""

import json
import random
import time
from datetime import datetime, timezone
from uuid import uuid4


CLIENTES = ["cliente-01", "cliente-02", "cliente-03", "cliente-04", "cliente-05"]
CIDADES = ["São Paulo", "Recife", "Curitiba", "Salvador"]


def gerar_transacao():
    return {
        "id": str(uuid4()),
        "cliente_id": random.choice(CLIENTES),
        "amount": random.randint(100, 1500000) / 100,
        "cidade": random.choice(CIDADES),
        "data_hora": datetime.now(timezone.utc).isoformat(),
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
