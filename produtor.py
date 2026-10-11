"""Gera uma transação a cada três segundos e publica no Kafka."""

import argparse
import json
import time

from confluent_kafka import Producer

from kafka_config import SERVIDOR, TOPICO, preparar_topico
from transacoes import gerar_transacao


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", type=int, default=0,
                        help="Quantidade a enviar; 0 executa até Ctrl+C.")
    args = parser.parse_args()
    preparar_topico()
    produtor = Producer({"bootstrap.servers": SERVIDOR, "enable.idempotence": True})
    erros = []

    def confirmar_envio(erro, mensagem):
        if erro is not None:
            erros.append(str(erro))

    print("Produtor conectado. Ctrl+C para encerrar.", flush=True)
    enviados = 0
    try:
        while args.limite == 0 or enviados < args.limite:
            inicio = time.monotonic()
            transacao = gerar_transacao()
            produtor.produce(
                TOPICO,
                key=transacao["cliente_id"].encode("utf-8"),
                value=json.dumps(transacao, ensure_ascii=False).encode("utf-8"),
                on_delivery=confirmar_envio,
            )
            pendentes = produtor.flush(15)
            if erros or pendentes:
                raise RuntimeError(f"Falha ao confirmar envio: {erros}, pendentes={pendentes}")
            print("ENVIADA:", json.dumps(transacao, ensure_ascii=False), flush=True)
            enviados += 1
            if args.limite and enviados >= args.limite:
                break
            time.sleep(max(0, 3 - (time.monotonic() - inicio)))
    except KeyboardInterrupt:
        print("\nProdutor encerrado.")
    finally:
        produtor.flush(5)


if __name__ == "__main__":
    main()
