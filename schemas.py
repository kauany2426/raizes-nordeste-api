from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr
from enums import Perfil, CanalPedido, StatusPedido, StatusPagamento, TipoMovimentacao


# schema genérico de paginação que vai ser usado em todas as listagens
class RespostaPaginada(BaseModel):
    dados: List[Any]
    pagina: int
    limite: int
    total: int
    total_paginas: int


# ---- autenticação ----

class RegistroInput(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    consentimento_lgpd: bool


class LoginInput(BaseModel):
    email: EmailStr
    senha: str


class RefreshTokenInput(BaseModel):
    refresh_token: str


class UsuarioResposta(BaseModel):
    id: int
    nome: str
    email: str
    perfil: Perfil
    pontos_fidelidade: int
    criado_em: datetime

    class Config:
        from_attributes = True


class TokenResposta(BaseModel):
    access_token: str
    refresh_token: str
    tipo: str = "Bearer"
    usuario: UsuarioResposta


# ---- usuários ----

class CriarUsuarioInput(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    perfil: Perfil = Perfil.CLIENTE
    consentimento_lgpd: bool = True


# ---- produtos ----

class CriarProdutoInput(BaseModel):
    nome: str
    descricao: Optional[str] = None
    categoria: Optional[str] = None


class AtualizarProdutoInput(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    categoria: Optional[str] = None
    ativo: Optional[bool] = None


class ProdutoResposta(BaseModel):
    id: int
    nome: str
    descricao: Optional[str]
    categoria: Optional[str]
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True


# ---- unidades ----

class CriarUnidadeInput(BaseModel):
    nome: str
    endereco: str


class AtualizarUnidadeInput(BaseModel):
    nome: Optional[str] = None
    endereco: Optional[str] = None
    ativa: Optional[bool] = None


class UnidadeResposta(BaseModel):
    id: int
    nome: str
    endereco: str
    ativa: bool
    criado_em: datetime

    class Config:
        from_attributes = True


# ---- estoque / cardápio ----

class AdicionarItemCardapioInput(BaseModel):
    produto_id: int
    preco_local: Decimal
    quantidade_inicial: int = 0


class AtualizarItemCardapioInput(BaseModel):
    preco_local: Optional[Decimal] = None
    quantidade_atual: Optional[int] = None
    disponivel: Optional[bool] = None


class ItemCardapioResposta(BaseModel):
    produto_id: int
    unidade_id: int
    preco_local: Decimal
    quantidade_atual: int
    disponivel: bool
    produto: ProdutoResposta

    class Config:
        from_attributes = True


class CriarMovimentacaoInput(BaseModel):
    produto_id: int
    tipo: TipoMovimentacao
    quantidade: int
    motivo: Optional[str] = None


class MovimentacaoResposta(BaseModel):
    id: int
    produto_id: int
    unidade_id: int
    tipo: TipoMovimentacao
    quantidade: int
    motivo: Optional[str]
    criado_em: datetime

    class Config:
        from_attributes = True


# ---- pedidos ----

class ItemPedidoInput(BaseModel):
    produto_id: int
    quantidade: int


class CriarPedidoInput(BaseModel):
    unidade_id: int
    canal_pedido: CanalPedido
    itens: List[ItemPedidoInput]
    usar_pontos: bool = False


class AtualizarStatusInput(BaseModel):
    novo_status: StatusPedido
    motivo: Optional[str] = None


class CancelarPedidoInput(BaseModel):
    motivo: Optional[str] = None


class ItemPedidoResposta(BaseModel):
    id: int
    produto_id: int
    quantidade: int
    preco_unitario: Decimal

    class Config:
        from_attributes = True


class PagamentoResposta(BaseModel):
    id: int
    valor: Decimal
    status: StatusPagamento
    numero_tentativa: int
    referencia_gateway: Optional[str]
    criado_em: datetime

    class Config:
        from_attributes = True


class PedidoResposta(BaseModel):
    id: int
    unidade_id: int
    canal_pedido: CanalPedido
    status: StatusPedido
    subtotal: Decimal
    desconto: Decimal
    total: Decimal
    itens: List[ItemPedidoResposta]
    pagamentos: List[PagamentoResposta]
    criado_em: datetime

    class Config:
        from_attributes = True
