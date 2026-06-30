from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import math
from database import get_db
from models import Usuario
from schemas import CriarUsuarioInput, UsuarioResposta, RespostaPaginada
from security import hash_senha
from deps import require_roles
from enums import Perfil

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.post("", response_model=UsuarioResposta, status_code=201)
def criar_usuario(
    dados: CriarUsuarioInput,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_roles(Perfil.ADMIN))
):
    # somente admin pode criar usuários com perfis específicos
    existe = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if existe:
        raise HTTPException(status_code=409, detail="Já existe um usuário com esse e-mail")

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        perfil=dados.perfil,
        consentimento_lgpd=dados.consentimento_lgpd
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.get("", response_model=RespostaPaginada)
def listar_usuarios(
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    gestor: Usuario = Depends(require_roles(Perfil.ADMIN, Perfil.GERENTE))
):
    total = db.query(Usuario).count()
    usuarios = db.query(Usuario).offset((pagina - 1) * limite).limit(limite).all()

    lista = [UsuarioResposta.model_validate(u) for u in usuarios]

    return RespostaPaginada(
        dados=lista,
        pagina=pagina,
        limite=limite,
        total=total,
        total_paginas=math.ceil(total / limite) if total > 0 else 1
    )


@router.get("/{usuario_id}", response_model=UsuarioResposta)
def buscar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    gestor: Usuario = Depends(require_roles(Perfil.ADMIN, Perfil.GERENTE))
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario


@router.delete("/{usuario_id}", status_code=204)
def remover_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_roles(Perfil.ADMIN))
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    db.delete(usuario)
    db.commit()
