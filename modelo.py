"""Formato do enunciado e compatibilidade com as mensagens do primeiro teste."""

from datetime import datetime, timedelta, timezone
from uuid import NAMESPACE_URL, UUID, uuid5


FUSO_HORARIO = timezone(timedelta(hours=-3))


def id_cliente_legado(nome):
    """Mantém o mesmo UUID para cada cliente entre execuções."""
    return str(uuid5(NAMESPACE_URL, f"deteccao-fraude/{nome}"))


def normalizar_transacao(dados):
    if "id_transacao" in dados:
        transacao = {campo: dados[campo] for campo in (
            "id_transacao", "id_cliente", "valor", "country", "city", "hora"
        )}
    else:
        # Mensagens antigas podem continuar no tópico depois da atualização.
        transacao = {
            "id_transacao": dados["id"],
            "id_cliente": id_cliente_legado(dados["cliente_id"]),
            "valor": dados["amount"],
            "country": "BR",
            "city": dados["cidade"],
            "hora": dados["data_hora"],
        }
    UUID(transacao["id_transacao"])
    UUID(transacao["id_cliente"])
    return transacao


def instante_transacao(hora):
    horario = datetime.fromisoformat(hora)
    # O modelo do professor não inclui o fuso. Neste exercício usamos UTC-03.
    if horario.tzinfo is None:
        horario = horario.replace(tzinfo=FUSO_HORARIO)
    return horario.timestamp()
