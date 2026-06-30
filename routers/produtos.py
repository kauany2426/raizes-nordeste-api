from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import math
from database import get_db
from models import Produto, Usuario
from schemas import CriarProdutoInput, AtualizarProdutoInput, ProdutoResposta, RespostaPaginada
from deps import require_roles, get_current_user
from enums import Perfil

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.post("", response_model=ProdutoResposta, status_code=201)
def criar_produto(
    dados: CriarProdutoInput,
    db: Session = Depends(get_db),
    gestor: Usuario = Depends(require_roles(Perfil.ADMIN, Perfil.GERENTE))
):
    produto = Produto(
        nome=dados.nome,
        descricao=dados.descricao,
        categoria=dados.categoria
    )
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


@router.get("", response_model=RespostaPaginada)
def listar_produtos(
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
    categoria: Optional[str] = Query(None),
    somente_ativos: bool = Query(True),
    db: Session = Depends(get_db)
):
    query = db.query(Produto)

    if somente_ativos:
        query = query.filter(Produto.ativo == True)

    if categoria:
        query = query.filter(Produto.categoria == categoria)

    total = query.count()
    produtos = query.offset((pagina - 1) * limite).limit(limite).all()

    return RespostaPaginada(
        dados=[ProdutoResposta.model_validate(p) for p in produtos],
        pagina=pagina,
        limite=limite,
        total=total,
        total_paginas=math.ceil(total / limite) if total > 0 else 1
    )


@router.get("/{produto_id}", response_model=ProdutoResposta)
def buscar_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto


@router.patch("/{produto_id}", response_model=ProdutoResposta)
def atualizar_produto(
    produto_id: int,
    dados: AtualizarProdutoInput,
    db: Session = Depends(get_db),
    gestor: Usuario = Depends(require_roles(Perfil.ADMIN, Perfil.GERENTE))
):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # atualiza apenas os campos que foram enviados
    if dados.nome is not None:
        produto.nome = dados.nome
    if dados.descricao is not None:
        produto.descricao = dados.descricao
    if dados.categoria is not None:
        produto.categoria = dados.categoria
    if dados.ativo is not None:
        produto.ativo = dados.ativo

    db.commit()
    db.refresh(produto)
    return produto


@router.patch("/{produto_id}/desativar", response_model=ProdutoResposta)
def desativar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    gestor: Usuario = Depends(require_roles(Perfil.ADMIN, Perfil.GERENTE))
):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    if not produto.ativo:
        raise HTTPException(status_code=409, detail="Produto já está inativo")

    produto.ativo = False
    db.commit()
    db.refresh(produto)
    return produto


@router.patch("/{produto_id}/ativar", response_model=ProdutoResposta)
def ativar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    gestor: Usuario = Depends(require_roles(Perfil.ADMIN, Perfil.GERENTE))
):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    if produto.ativo:
        raise HTTPException(status_code=409, detail="Produto já está ativo")

    produto.ativo = True
    db.commit()
    db.refresh(produto)
    return produto
