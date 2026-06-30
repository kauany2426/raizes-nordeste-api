from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import math
from database import get_db
from models import Unidade, Usuario
from schemas import CriarUnidadeInput, AtualizarUnidadeInput, UnidadeResposta, RespostaPaginada
from deps import require_roles
from enums import Perfil

router = APIRouter(prefix="/unidades", tags=["Unidades"])


@router.post("", response_model=UnidadeResposta, status_code=201)
def criar_unidade(
    dados: CriarUnidadeInput,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_roles(Perfil.ADMIN))
):
    unidade = Unidade(nome=dados.nome, endereco=dados.endereco)
    db.add(unidade)
    db.commit()
    db.refresh(unidade)
    return unidade


@router.get("", response_model=RespostaPaginada)
def listar_unidades(
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
    somente_ativas: bool = Query(True),
    db: Session = Depends(get_db)
):
    query = db.query(Unidade)

    if somente_ativas:
        query = query.filter(Unidade.ativa == True)

    total = query.count()
    unidades = query.offset((pagina - 1) * limite).limit(limite).all()

    return RespostaPaginada(
        dados=[UnidadeResposta.model_validate(u) for u in unidades],
        pagina=pagina,
        limite=limite,
        total=total,
        total_paginas=math.ceil(total / limite) if total > 0 else 1
    )


@router.get("/{unidade_id}", response_model=UnidadeResposta)
def buscar_unidade(unidade_id: int, db: Session = Depends(get_db)):
    unidade = db.query(Unidade).filter(Unidade.id == unidade_id).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")
    return unidade


@router.patch("/{unidade_id}", response_model=UnidadeResposta)
def atualizar_unidade(
    unidade_id: int,
    dados: AtualizarUnidadeInput,
    db: Session = Depends(get_db),
    gestor: Usuario = Depends(require_roles(Perfil.ADMIN, Perfil.GERENTE))
):
    unidade = db.query(Unidade).filter(Unidade.id == unidade_id).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")

    if dados.nome is not None:
        unidade.nome = dados.nome
    if dados.endereco is not None:
        unidade.endereco = dados.endereco
    if dados.ativa is not None:
        unidade.ativa = dados.ativa

    db.commit()
    db.refresh(unidade)
    return unidade
