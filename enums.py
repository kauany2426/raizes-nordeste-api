from enum import Enum


class Perfil(str, Enum):
    CLIENTE = "CLIENTE"
    ATENDENTE = "ATENDENTE"
    COZINHA = "COZINHA"
    GERENTE = "GERENTE"
    ADMIN = "ADMIN"


class CanalPedido(str, Enum):
    APP = "APP"
    TOTEM = "TOTEM"
    BALCAO = "BALCAO"
    PICKUP = "PICKUP"
    WEB = "WEB"


class StatusPedido(str, Enum):
    AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    EM_PREPARO = "EM_PREPARO"
    PRONTO = "PRONTO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"


class StatusPagamento(str, Enum):
    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    RECUSADO = "RECUSADO"


class TipoMovimentacao(str, Enum):
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"


TRANSICOES_VALIDAS: dict[StatusPedido, list[StatusPedido]] = {
    StatusPedido.AGUARDANDO_PAGAMENTO: [StatusPedido.EM_PREPARO, StatusPedido.CANCELADO],
    StatusPedido.EM_PREPARO: [StatusPedido.PRONTO, StatusPedido.CANCELADO],
    StatusPedido.PRONTO: [StatusPedido.ENTREGUE, StatusPedido.CANCELADO],
    StatusPedido.ENTREGUE: [],
    StatusPedido.CANCELADO: [],
}


def transicao_valida(atual: StatusPedido, novo: StatusPedido) -> bool:
    return novo in TRANSICOES_VALIDAS.get(atual, [])
