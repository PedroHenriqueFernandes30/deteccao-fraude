"""Recebe transações, salva em SQLite e exibe alertas de possível fraude."""

import argparse
import json

from confluent_kafka import Consumer, KafkaException

from kafka_config import SERVIDOR, TOPICO, preparar_topico
from banco import CAMINHO_BANCO, abrir_banco, salvar_transacao


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", type=int, default=0,
                        help="Quantidade a receber; 0 executa até Ctrl+C.")
    args = parser.parse_args()
    preparar_topico()
    consumidor = Consumer({
        "bootstrap.servers": SERVIDOR,
        # Grupo novo para também salvar mensagens do primeiro teste, ainda no Kafka.
        "group.id": "detector-fraude-com-banco",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    banco = abrir_banco()
    consumidor.subscribe([TOPICO])
    print("Consumidor aguardando transações. Ctrl+C para encerrar.", flush=True)
    print(f"Banco de dados: {CAMINHO_BANCO}", flush=True)
    recebidas = 0
    try:
        while args.limite == 0 or recebidas < args.limite:
            mensagem = consumidor.poll(1)
            if mensagem is None:
                continue
            if mensagem.error():
                raise KafkaException(mensagem.error())
            transacao = json.loads(mensagem.value().decode("utf-8"))
            alertas, nova = salvar_transacao(banco, transacao)
            print("\nRECEBIDA:", json.dumps(transacao, ensure_ascii=False), flush=True)
            print("BANCO:", "salva" if nova else "já registrada", flush=True)
            print("ALERTAS:", ", ".join(alertas) if alertas else "nenhum", flush=True)
            # Só confirma no Kafka depois que o banco concluiu a gravação.
            consumidor.commit(message=mensagem, asynchronous=False)
            recebidas += 1
    except KeyboardInterrupt:
        print("\nConsumidor encerrado.")
    finally:
        consumidor.close()
        banco.close()


if __name__ == "__main__":
    main()
