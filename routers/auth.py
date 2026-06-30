from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError
from database import get_db
from models import Usuario
from schemas import RegistroInput, LoginInput, RefreshTokenInput, TokenResposta, UsuarioResposta
from security import hash_senha, verificar_senha, criar_access_token, criar_refresh_token, decodificar_refresh_token
from deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/registro", response_model=UsuarioResposta, status_code=201)
def registrar(dados: RegistroInput, db: Session = Depends(get_db)):
    # verifica se o consentimento LGPD foi dado
    if not dados.consentimento_lgpd:
        raise HTTPException(status_code=400, detail="O consentimento LGPD é obrigatório")

    # verifica se a senha tem pelo menos 6 caracteres
    if len(dados.senha) < 6:
        raise HTTPException(status_code=422, detail="A senha precisa ter pelo menos 6 caracteres")

    # verifica se o email já está em uso
    existe = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if existe:
        raise HTTPException(status_code=409, detail="Já existe uma conta com esse e-mail")

    novo_usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        consentimento_lgpd=dados.consentimento_lgpd
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario


@router.post("/login", response_model=TokenResposta)
def login(dados: LoginInput, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()

    # se não achou o usuário ou a senha está errada, retorna 401
    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")

    access_token = criar_access_token({"sub": str(usuario.id), "perfil": usuario.perfil.value})
    refresh_token = criar_refresh_token({"sub": str(usuario.id)})

    # salva o hash do refresh token no banco
    usuario.refresh_token_hash = hash_senha(refresh_token)
    db.commit()
    db.refresh(usuario)

    return TokenResposta(access_token=access_token, refresh_token=refresh_token, usuario=usuario)


@router.post("/refresh", response_model=TokenResposta)
def renovar_token(dados: RefreshTokenInput, db: Session = Depends(get_db)):
    try:
        payload = decodificar_refresh_token(dados.refresh_token)
        usuario_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.refresh_token_hash:
        raise HTTPException(status_code=401, detail="Sessão encerrada, faça login novamente")

    if not verificar_senha(dados.refresh_token, usuario.refresh_token_hash):
        raise HTTPException(status_code=401, detail="Refresh token não é válido")

    # gera novos tokens
    novo_access = criar_access_token({"sub": str(usuario.id), "perfil": usuario.perfil.value})
    novo_refresh = criar_refresh_token({"sub": str(usuario.id)})

    usuario.refresh_token_hash = hash_senha(novo_refresh)
    db.commit()
    db.refresh(usuario)

    return TokenResposta(access_token=novo_access, refresh_token=novo_refresh, usuario=usuario)


@router.post("/logout", status_code=204)
def logout(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    # limpa o refresh token para invalidar a sessão
    usuario.refresh_token_hash = None
    db.commit()


@router.get("/me", response_model=UsuarioResposta)
def meu_perfil(usuario: Usuario = Depends(get_current_user)):
    return usuario
