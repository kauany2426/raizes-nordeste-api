from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from datetime import datetime
import uuid

from database import Base, engine
from config import configuracoes
from routers import auth, usuarios, produtos, unidades, estoque, pedidos, pagamentos

# cria as tabelas no banco se ainda não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Raízes do Nordeste",
    description="API de gerenciamento de pedidos da rede de lanchonetes Raízes do Nordeste",
    version="1.0.0"
)

# libera o CORS para qualquer origem (em produção seria mais restrito)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# registra todos os routers
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(produtos.router)
app.include_router(unidades.router)
app.include_router(estoque.router)
app.include_router(pedidos.router)
app.include_router(pagamentos.router)


# handler de erros de validação (campos inválidos, tipos errados, etc.)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    detalhes = []
    for erro in exc.errors():
        campo = ".".join(str(x) for x in erro["loc"] if x != "body")
        detalhes.append({"campo": campo, "problema": erro["msg"]})

    return JSONResponse(
        status_code=422,
        content={
            "erro": "ERRO_DE_VALIDACAO",
            "mensagem": "Os dados enviados são inválidos",
            "detalhes": detalhes,
            "timestamp": datetime.utcnow().isoformat(),
            "caminho": str(request.url.path),
            "request_id": str(uuid.uuid4())
        }
    )


# handler geral para qualquer outro erro HTTP
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    from fastapi import HTTPException

    if isinstance(exc, HTTPException):
        erros_por_status = {
            400: "REQUISICAO_INVALIDA",
            401: "NAO_AUTENTICADO",
            403: "SEM_PERMISSAO",
            404: "NAO_ENCONTRADO",
            409: "CONFLITO",
            422: "ERRO_DE_VALIDACAO",
        }
        nome_erro = erros_por_status.get(exc.status_code, "ERRO_INTERNO")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "erro": nome_erro,
                "mensagem": exc.detail,
                "detalhes": [],
                "timestamp": datetime.utcnow().isoformat(),
                "caminho": str(request.url.path),
                "request_id": str(uuid.uuid4())
            }
        )

    # erro inesperado
    return JSONResponse(
        status_code=500,
        content={
            "erro": "ERRO_INTERNO",
            "mensagem": "Ocorreu um erro inesperado no servidor",
            "detalhes": [],
            "timestamp": datetime.utcnow().isoformat(),
            "caminho": str(request.url.path),
            "request_id": str(uuid.uuid4())
        }
    )


@app.get("/", tags=["Status"])
def status():
    return {"status": "online", "mensagem": "API Raízes do Nordeste funcionando"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=configuracoes.PORT, reload=True)
