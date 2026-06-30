from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import configuracoes

# pg8000 é driver puro Python, não precisa compilar nada
# então funciona em qualquer versão do Python incluindo 3.13
url = configuracoes.DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)
engine = create_engine(url)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
