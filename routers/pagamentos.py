from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
import uuid
import random
from database import get_db
from models import Pedido, Pagamento, HistoricoStatusPedido, Usuario
from schemas import PagamentoResposta
from deps import get_current_user
from enums import StatusPedido, StatusPagamento, Perfil

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])


def gateway_mock(numero_tentativa: int) -> dict:
    """
    Simula o retorno de um gateway de pagamento externo.
    80% de chance de aprovação, 20% de recusa (instabilidade do gateway).
    Na segunda tentativa em diante a chance de aprovação sobe para 95%.
    """
    referencia = str(uuid.uuid4())[:8].upper()

    # na primeira tentativa tem 80% de chance de aprovar
    # nas tentativas seguintes sobe para 95% (gateway estabilizou)
    chance_aprovacao = 0.80 if numero_tentativa == 1 else 0.95
    aprovado = random.random() < chance_aprovacao

    if aprovado:
        return {"aprovado": True, "referencia": referencia, "mensagem": "Pagamento aprovado pelo gateway"}
    else:
        return {"aprovado": False, "referencia": referencia, "mensagem": "Gateway indisponível no momento. Tente novamente."}


@router.post("/{pedido_id}/processar", response_model=PagamentoResposta)
def processar_pagamento(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(get_current_user)
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    # cliente só pode processar pagamento do próprio pedido
    if usuario_logado.perfil == Perfil.CLIENTE and pedido.cliente_id != usuario_logado.id:
        raise HTTPException(status_code=403, detail="Você não tem acesso a este pedido")

    if pedido.status != StatusPedido.AGUARDANDO_PAGAMENTO:
        raise HTTPException(
            status_code=409,
            detail=f"Não é possível processar pagamento de um pedido com status {pedido.status.value}"
        )

    # busca o pagamento pendente mais recente
    pagamento = db.query(Pagamento).filter(
        Pagamento.pedido_id == pedido_id,
        Pagamento.status == StatusPagamento.PENDENTE
    ).order_by(Pagamento.numero_tentativa.desc()).first()

    if not pagamento:
        raise HTTPException(status_code=404, detail="Nenhum pagamento pendente encontrado para este pedido")

    # envia para o gateway (mock) e recebe o resultado
    resultado = gateway_mock(pagamento.numero_tentativa)

    pagamento.referencia_gateway = resultado["referencia"]

    if resultado["aprovado"]:
        pagamento.status = StatusPagamento.APROVADO

        # move o pedido para em preparo após pagamento aprovado
        status_anterior = pedido.status.value
        pedido.status = StatusPedido.EM_PREPARO

        historico = HistoricoStatusPedido(
            pedido_id=pedido.id,
            status_anterior=status_anterior,
            novo_status=StatusPedido.EM_PREPARO.value,
            motivo="Pagamento aprovado pelo gateway"
        )
        db.add(historico)

        # dá pontos de fidelidade ao cliente (1 ponto por R$ 1,00)
        if pedido.cliente_id:
            cliente = db.query(Usuario).filter(Usuario.id == pedido.cliente_id).first()
            if cliente:
                pontos_ganhos = int(pedido.total)
                cliente.pontos_fidelidade += pontos_ganhos

    else:
        pagamento.status = StatusPagamento.RECUSADO

    db.commit()
    db.refresh(pagamento)
    return pagamento


@router.post("/{pedido_id}/nova-tentativa", response_model=PagamentoResposta, status_code=201)
def nova_tentativa_pagamento(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(get_current_user)
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    if usuario_logado.perfil == Perfil.CLIENTE and pedido.cliente_id != usuario_logado.id:
        raise HTTPException(status_code=403, detail="Você não tem acesso a este pedido")

    if pedido.status != StatusPedido.AGUARDANDO_PAGAMENTO:
        raise HTTPException(status_code=409, detail="Este pedido não está aguardando pagamento")

    # verifica se ainda tem algum pagamento pendente (não deixa criar duplicado)
    pendente = db.query(Pagamento).filter(
        Pagamento.pedido_id == pedido_id,
        Pagamento.status == StatusPagamento.PENDENTE
    ).first()
    if pendente:
        raise HTTPException(status_code=409, detail="Já existe uma tentativa de pagamento pendente para este pedido")

    # pega o número da última tentativa para incrementar
    ultima = db.query(Pagamento).filter(
        Pagamento.pedido_id == pedido_id
    ).order_by(Pagamento.numero_tentativa.desc()).first()

    proxima_tentativa = (ultima.numero_tentativa + 1) if ultima else 1

    novo_pagamento = Pagamento(
        pedido_id=pedido_id,
        valor=pedido.total,
        numero_tentativa=proxima_tentativa
    )
    db.add(novo_pagamento)
    db.commit()
    db.refresh(novo_pagamento)
    return novo_pagamento


@router.get("/{pedido_id}", response_model=list[PagamentoResposta])
def listar_pagamentos(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(get_current_user)
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    if usuario_logado.perfil == Perfil.CLIENTE and pedido.cliente_id != usuario_logado.id:
        raise HTTPException(status_code=403, detail="Você não tem acesso a este pedido")

    pagamentos = db.query(Pagamento).filter(
        Pagamento.pedido_id == pedido_id
    ).order_by(Pagamento.numero_tentativa).all()

    return pagamentos
