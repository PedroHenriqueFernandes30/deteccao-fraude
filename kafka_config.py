"""Configuração compartilhada pelos dois programas."""

import os

from confluent_kafka import KafkaError
from confluent_kafka.admin import AdminClient, NewTopic


SERVIDOR = os.getenv("KAFKA_SERVIDOR", "localhost:9092")
TOPICO = os.getenv("KAFKA_TOPICO", "transacoes")


def preparar_topico():
    admin = AdminClient({"bootstrap.servers": SERVIDOR})
    resultados = admin.create_topics(
        [NewTopic(TOPICO, num_partitions=1, replication_factor=1)],
        request_timeout=15,
    )
    try:
        resultados[TOPICO].result()
    except Exception as erro:
        if not erro.args or not hasattr(erro.args[0], "code"):
            raise
        if erro.args[0].code() != KafkaError.TOPIC_ALREADY_EXISTS:
            raise
