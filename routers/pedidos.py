from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
import math
from database import get_db
from models import Pedido, ItemPedido, ItemCardapio, Unidade, MovimentacaoEstoque, HistoricoStatusPedido, Pagamento, Usuario
from schemas import CriarPedidoInput, AtualizarStatusInput, CancelarPedidoInput, PedidoResposta, RespostaPaginada
from deps import get_current_user, require_roles
from enums import Perfil, StatusPedido, TipoMovimentacao, StatusPagamento, CanalPedido
from enums import transicao_valida

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.post("", response_model=PedidoResposta, status_code=201)
def criar_pedido(
    dados: CriarPedidoInput,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(get_current_user)
):
    if not dados.itens:
        raise HTTPException(status_code=422, detail="O pedido precisa ter pelo menos um item")

    # verifica se a unidade existe e está ativa
    unidade = db.query(Unidade).filter(Unidade.id == dados.unidade_id).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")
    if not unidade.ativa:
        raise HTTPException(status_code=409, detail="Esta unidade não está ativa")

    # verifica cada item e busca o preço no cardápio da unidade
    itens_validados = []
    for item_input in dados.itens:
        item_cardapio = db.query(ItemCardapio).filter(
            ItemCardapio.unidade_id == dados.unidade_id,
            ItemCardapio.produto_id == item_input.produto_id
        ).first()

        if not item_cardapio:
            raise HTTPException(
                status_code=404,
                detail=f"Produto {item_input.produto_id} não encontrado no cardápio desta unidade"
            )
        if not item_cardapio.disponivel:
            raise HTTPException(
                status_code=409,
                detail=f"Produto {item_input.produto_id} não está disponível no momento"
            )
        if item_cardapio.quantidade_atual < item_input.quantidade:
            raise HTTPException(
                status_code=409,
                detail=f"Estoque insuficiente para o produto {item_input.produto_id}. Disponível: {item_cardapio.quantidade_atual}"
            )

        itens_validados.append({
            "produto_id": item_input.produto_id,
            "quantidade": item_input.quantidade,
            "preco_unitario": item_cardapio.preco_local,
            "item_cardapio": item_cardapio
        })

    # calcula o subtotal somando preço * quantidade de cada item
    subtotal = sum(
        item["preco_unitario"] * item["quantidade"]
        for item in itens_validados
    )

    desconto = Decimal("0.00")

    # aplica desconto de pontos de fidelidade se solicitado
    if dados.usar_pontos and usuario_logado.pontos_fidelidade > 0:
        # 100 pontos = R$ 1,00 de desconto
        desconto_maximo = (subtotal * Decimal("0.5")).quantize(Decimal("0.01"))
        desconto_pelos_pontos = Decimal(usuario_logado.pontos_fidelidade // 100)

        desconto = min(desconto_pelos_pontos, desconto_maximo)
        pontos_usados = int(desconto * 100)
        usuario_logado.pontos_fidelidade -= pontos_usados

    total = subtotal - desconto

    try:
        # cria o pedido
        pedido = Pedido(
            cliente_id=usuario_logado.id,
            unidade_id=dados.unidade_id,
            canal_pedido=dados.canal_pedido,
            subtotal=subtotal,
            desconto=desconto,
            total=total
        )
        db.add(pedido)
        db.flush()  # precisa do id do pedido antes de criar os itens

        # cria os itens do pedido e baixa o estoque
        for item in itens_validados:
            item_pedido = ItemPedido(
                pedido_id=pedido.id,
                produto_id=item["produto_id"],
                quantidade=item["quantidade"],
                preco_unitario=item["preco_unitario"]
            )
            db.add(item_pedido)

            # baixa o estoque do produto na unidade
            item["item_cardapio"].quantidade_atual -= item["quantidade"]

            # registra a movimentação de saída no estoque
            mov = MovimentacaoEstoque(
                produto_id=item["produto_id"],
                unidade_id=dados.unidade_id,
                tipo=TipoMovimentacao.SAIDA,
                quantidade=item["quantidade"],
                motivo=f"Saída pelo pedido #{pedido.id}",
                usuario_id=usuario_logado.id
            )
            db.add(mov)

        # registra o status inicial no histórico
        historico = HistoricoStatusPedido(
            pedido_id=pedido.id,
            status_anterior=None,
            novo_status=StatusPedido.AGUARDANDO_PAGAMENTO.value,
            motivo="Pedido criado"
        )
        db.add(historico)

        # cria o registro de pagamento pendente
        pagamento = Pagamento(
            pedido_id=pedido.id,
            valor=total,
            numero_tentativa=1
        )
        db.add(pagamento)

        db.commit()
        db.refresh(pedido)
        return pedido

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao criar o pedido. Tente novamente.")


@router.get("", response_model=RespostaPaginada)
def listar_pedidos(
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
    canal_pedido: Optional[CanalPedido] = Query(None),
    status: Optional[StatusPedido] = Query(None),
    unidade_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(get_current_user)
):
    query = db.query(Pedido)

    # cliente só vê os próprios pedidos
    if usuario_logado.perfil == Perfil.CLIENTE:
        query = query.filter(Pedido.cliente_id == usuario_logado.id)

    if canal_pedido:
        query = query.filter(Pedido.canal_pedido == canal_pedido)
    if status:
        query = query.filter(Pedido.status == status)
    if unidade_id:
        query = query.filter(Pedido.unidade_id == unidade_id)

    query = query.order_by(Pedido.criado_em.desc())
    total = query.count()
    pedidos = query.offset((pagina - 1) * limite).limit(limite).all()

    return RespostaPaginada(
        dados=[PedidoResposta.model_validate(p) for p in pedidos],
        pagina=pagina,
        limite=limite,
        total=total,
        total_paginas=math.ceil(total / limite) if total > 0 else 1
    )


@router.get("/{pedido_id}", response_model=PedidoResposta)
def buscar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(get_current_user)
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    # cliente só pode ver o próprio pedido
    if usuario_logado.perfil == Perfil.CLIENTE and pedido.cliente_id != usuario_logado.id:
        raise HTTPException(status_code=403, detail="Você não tem acesso a este pedido")

    return pedido


@router.patch("/{pedido_id}/status", response_model=PedidoResposta)
def atualizar_status(
    pedido_id: int,
    dados: AtualizarStatusInput,
    db: Session = Depends(get_db),
    funcionario: Usuario = Depends(require_roles(Perfil.COZINHA, Perfil.ATENDENTE, Perfil.GERENTE, Perfil.ADMIN))
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    # valida se a transição de status é permitida
    if not transicao_valida(pedido.status, dados.novo_status):
        raise HTTPException(
            status_code=409,
            detail=f"Não é possível mudar o status de {pedido.status.value} para {dados.novo_status.value}"
        )

    status_anterior = pedido.status.value
    pedido.status = dados.novo_status

    # registra a mudança no histórico
    historico = HistoricoStatusPedido(
        pedido_id=pedido.id,
        status_anterior=status_anterior,
        novo_status=dados.novo_status.value,
        motivo=dados.motivo
    )
    db.add(historico)
    db.commit()
    db.refresh(pedido)
    return pedido


@router.post("/{pedido_id}/cancelar", response_model=PedidoResposta)
def cancelar_pedido(
    pedido_id: int,
    dados: CancelarPedidoInput,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(get_current_user)
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    # cliente só pode cancelar o próprio pedido e somente se ainda está aguardando pagamento
    if usuario_logado.perfil == Perfil.CLIENTE:
        if pedido.cliente_id != usuario_logado.id:
            raise HTTPException(status_code=403, detail="Você não tem acesso a este pedido")
        if pedido.status != StatusPedido.AGUARDANDO_PAGAMENTO:
            raise HTTPException(status_code=409, detail="Você só pode cancelar pedidos que ainda estão aguardando pagamento")

    # verifica se o pedido já está em status terminal
    if pedido.status in [StatusPedido.ENTREGUE, StatusPedido.CANCELADO]:
        raise HTTPException(
            status_code=409,
            detail=f"Não é possível cancelar um pedido com status {pedido.status.value}"
        )

    status_anterior = pedido.status.value
    pedido.status = StatusPedido.CANCELADO

    # devolve o estoque dos itens cancelados
    for item in pedido.itens:
        item_cardapio = db.query(ItemCardapio).filter(
            ItemCardapio.unidade_id == pedido.unidade_id,
            ItemCardapio.produto_id == item.produto_id
        ).first()

        if item_cardapio:
            item_cardapio.quantidade_atual += item.quantidade

            mov = MovimentacaoEstoque(
                produto_id=item.produto_id,
                unidade_id=pedido.unidade_id,
                tipo=TipoMovimentacao.ENTRADA,
                quantidade=item.quantidade,
                motivo=f"Estorno pelo cancelamento do pedido #{pedido.id}",
                usuario_id=usuario_logado.id
            )
            db.add(mov)

    # devolve os pontos caso o cliente tenha usado desconto
    if pedido.desconto > 0 and pedido.cliente_id:
        cliente = db.query(Usuario).filter(Usuario.id == pedido.cliente_id).first()
        if cliente:
            pontos_devolver = int(pedido.desconto * 100)
            cliente.pontos_fidelidade += pontos_devolver

    historico = HistoricoStatusPedido(
        pedido_id=pedido.id,
        status_anterior=status_anterior,
        novo_status=StatusPedido.CANCELADO.value,
        motivo=dados.motivo or "Pedido cancelado"
    )
    db.add(historico)
    db.commit()
    db.refresh(pedido)
    return pedido
