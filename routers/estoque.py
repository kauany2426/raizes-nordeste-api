from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import math
from database import get_db
from models import Unidade, Produto, ItemCardapio, MovimentacaoEstoque, Usuario
from schemas import (
    AdicionarItemCardapioInput, AtualizarItemCardapioInput, ItemCardapioResposta,
    CriarMovimentacaoInput, MovimentacaoResposta, RespostaPaginada
)
from deps import require_roles, get_current_user
from enums import Perfil, TipoMovimentacao

router = APIRouter(prefix="/unidades", tags=["Estoque e Cardápio"])


# ---- cardápio por unidade ----

@router.post("/{unidade_id}/cardapio", response_model=ItemCardapioResposta, status_code=201)
def adicionar_item_cardapio(
    unidade_id: int,
    dados: AdicionarItemCardapioInput,
    db: Session = Depends(get_db),
    gestor: Usuario = Depends(require_roles(Perfil.ADMIN, Perfil.GERENTE))
):
    # verifica se a unidade existe
    unidade = db.query(Unidade).filter(Unidade.id == unidade_id).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")

    # verifica se o produto existe
    produto = db.query(Produto).filter(Produto.id == dados.produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # verifica se o produto já está no cardápio dessa unidade
    ja_existe = db.query(ItemCardapio).filter(
        ItemCardapio.produto_id == dados.produto_id,
        ItemCardapio.unidade_id == unidade_id
    ).first()
    if ja_existe:
        raise HTTPException(status_code=409, detail="Produto já está no cardápio desta unidade")

    item = ItemCardapio(
        produto_id=dados.produto_id,
        unidade_id=unidade_id,
        preco_local=dados.preco_local,
        quantidade_atual=dados.quantidade_inicial
    )
    db.add(item)

    # se veio quantidade inicial, registra a movimentação de entrada
    if dados.quantidade_inicial > 0:
        mov = MovimentacaoEstoque(
            produto_id=dados.produto_id,
            unidade_id=unidade_id,
            tipo=TipoMovimentacao.ENTRADA,
            quantidade=dados.quantidade_inicial,
            motivo="Estoque inicial ao adicionar produto no cardápio",
            usuario_id=gestor.id
        )
        db.add(mov)

    db.commit()
    db.refresh(item)
    return item


@router.get("/{unidade_id}/cardapio", response_model=RespostaPaginada)
def listar_cardapio(
    unidade_id: int,
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
    somente_disponiveis: bool = Query(False),
    db: Session = Depends(get_db)
):
    unidade = db.query(Unidade).filter(Unidade.id == unidade_id).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")

    query = db.query(ItemCardapio).filter(ItemCardapio.unidade_id == unidade_id)

    if somente_disponiveis:
        query = query.filter(ItemCardapio.disponivel == True)

    total = query.count()
    itens = query.offset((pagina - 1) * limite).limit(limite).all()

    return RespostaPaginada(
        dados=[ItemCardapioResposta.model_validate(i) for i in itens],
        pagina=pagina,
        limite=limite,
        total=total,
        total_paginas=math.ceil(total / limite) if total > 0 else 1
    )


@router.patch("/{unidade_id}/cardapio/{produto_id}", response_model=ItemCardapioResposta)
def atualizar_item_cardapio(
    unidade_id: int,
    produto_id: int,
    dados: AtualizarItemCardapioInput,
    db: Session = Depends(get_db),
    gestor: Usuario = Depends(require_roles(Perfil.ADMIN, Perfil.GERENTE))
):
    item = db.query(ItemCardapio).filter(
        ItemCardapio.unidade_id == unidade_id,
        ItemCardapio.produto_id == produto_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado no cardápio desta unidade")

    if dados.preco_local is not None:
        item.preco_local = dados.preco_local
    if dados.quantidade_atual is not None:
        item.quantidade_atual = dados.quantidade_atual
    if dados.disponivel is not None:
        item.disponivel = dados.disponivel

    db.commit()
    db.refresh(item)
    return item


# ---- movimentações de estoque ----

@router.post("/{unidade_id}/estoque", response_model=MovimentacaoResposta, status_code=201)
def registrar_movimentacao(
    unidade_id: int,
    dados: CriarMovimentacaoInput,
    db: Session = Depends(get_db),
    gestor: Usuario = Depends(require_roles(Perfil.ADMIN, Perfil.GERENTE))
):
    unidade = db.query(Unidade).filter(Unidade.id == unidade_id).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")

    item = db.query(ItemCardapio).filter(
        ItemCardapio.unidade_id == unidade_id,
        ItemCardapio.produto_id == dados.produto_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Produto não encontrado no cardápio desta unidade")

    # para saída verifica se tem estoque suficiente
    if dados.tipo == TipoMovimentacao.SAIDA:
        if item.quantidade_atual < dados.quantidade:
            raise HTTPException(
                status_code=409,
                detail=f"Estoque insuficiente. Disponível: {item.quantidade_atual}"
            )
        item.quantidade_atual -= dados.quantidade
    else:
        item.quantidade_atual += dados.quantidade

    movimentacao = MovimentacaoEstoque(
        produto_id=dados.produto_id,
        unidade_id=unidade_id,
        tipo=dados.tipo,
        quantidade=dados.quantidade,
        motivo=dados.motivo,
        usuario_id=gestor.id
    )
    db.add(movimentacao)
    db.commit()
    db.refresh(movimentacao)
    return movimentacao


@router.get("/{unidade_id}/estoque", response_model=RespostaPaginada)
def listar_movimentacoes(
    unidade_id: int,
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
    produto_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    gestor: Usuario = Depends(require_roles(Perfil.ADMIN, Perfil.GERENTE))
):
    query = db.query(MovimentacaoEstoque).filter(MovimentacaoEstoque.unidade_id == unidade_id)

    if produto_id:
        query = query.filter(MovimentacaoEstoque.produto_id == produto_id)

    query = query.order_by(MovimentacaoEstoque.criado_em.desc())
    total = query.count()
    movs = query.offset((pagina - 1) * limite).limit(limite).all()

    return RespostaPaginada(
        dados=[MovimentacaoResposta.model_validate(m) for m in movs],
        pagina=pagina,
        limite=limite,
        total=total,
        total_paginas=math.ceil(total / limite) if total > 0 else 1
    )
