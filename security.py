from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from config import configuracoes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)


def verificar_senha(senha: str, hash: str) -> bool:
    return pwd_context.verify(senha, hash)


def criar_access_token(dados: dict) -> str:
    payload = dados.copy()
    expira = datetime.now(timezone.utc) + timedelta(minutes=configuracoes.JWT_EXPIRES_MINUTES)
    payload.update({"exp": expira, "tipo": "access"})
    return jwt.encode(payload, configuracoes.JWT_SECRET, algorithm="HS256")


def criar_refresh_token(dados: dict) -> str:
    payload = dados.copy()
    expira = datetime.now(timezone.utc) + timedelta(days=configuracoes.JWT_REFRESH_EXPIRES_DAYS)
    payload.update({"exp": expira, "tipo": "refresh"})
    return jwt.encode(payload, configuracoes.JWT_REFRESH_SECRET, algorithm="HS256")


def decodificar_access_token(token: str) -> dict:
    return jwt.decode(token, configuracoes.JWT_SECRET, algorithms=["HS256"])


def decodificar_refresh_token(token: str) -> dict:
    return jwt.decode(token, configuracoes.JWT_REFRESH_SECRET, algorithms=["HS256"])
