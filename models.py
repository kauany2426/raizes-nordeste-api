from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Integer, String, Boolean, Numeric, DateTime, Text,
    ForeignKey, Enum as SAEnum, UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from enums import Perfil, CanalPedido, StatusPedido, StatusPagamento, TipoMovimentacao


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[Perfil] = mapped_column(SAEnum(Perfil), default=Perfil.CLIENTE)
    consentimento_lgpd: Mapped[bool] = mapped_column(Boolean, default=False)
    pontos_fidelidade: Mapped[int] = mapped_column(Integer, default=0)
    refresh_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    pedidos: Mapped[list["Pedido"]] = relationship("Pedido", back_populates="cliente")
    movimentacoes: Mapped[list["MovimentacaoEstoque"]] = relationship("MovimentacaoEstoque", back_populates="usuario")


class Unidade(Base):
    __tablename__ = "unidades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(150))
    endereco: Mapped[str] = mapped_column(String(300))
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    itens_cardapio: Mapped[list["ItemCardapio"]] = relationship("ItemCardapio", back_populates="unidade")
    pedidos: Mapped[list["Pedido"]] = relationship("Pedido", back_populates="unidade")
    movimentacoes: Mapped[list["MovimentacaoEstoque"]] = relationship("MovimentacaoEstoque", back_populates="unidade")


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(150))
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    categoria: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    itens_cardapio: Mapped[list["ItemCardapio"]] = relationship("ItemCardapio", back_populates="produto")
    movimentacoes: Mapped[list["MovimentacaoEstoque"]] = relationship("MovimentacaoEstoque", back_populates="produto")


class ItemCardapio(Base):
    """Produto disponível em uma unidade específica, com preço e estoque próprios."""
    __tablename__ = "itens_cardapio"

    produto_id: Mapped[int] = mapped_column(Integer, ForeignKey("produtos.id"), primary_key=True)
    unidade_id: Mapped[int] = mapped_column(Integer, ForeignKey("unidades.id"), primary_key=True)
    preco_local: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantidade_atual: Mapped[int] = mapped_column(Integer, default=0)
    disponivel: Mapped[bool] = mapped_column(Boolean, default=True)

    produto: Mapped["Produto"] = relationship("Produto", back_populates="itens_cardapio")
    unidade: Mapped["Unidade"] = relationship("Unidade", back_populates="itens_cardapio")


class MovimentacaoEstoque(Base):
    __tablename__ = "movimentacoes_estoque"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    produto_id: Mapped[int] = mapped_column(Integer, ForeignKey("produtos.id"))
    unidade_id: Mapped[int] = mapped_column(Integer, ForeignKey("unidades.id"))
    tipo: Mapped[TipoMovimentacao] = mapped_column(SAEnum(TipoMovimentacao))
    quantidade: Mapped[int] = mapped_column(Integer)
    motivo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    usuario_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    produto: Mapped["Produto"] = relationship("Produto", back_populates="movimentacoes")
    unidade: Mapped["Unidade"] = relationship("Unidade", back_populates="movimentacoes")
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="movimentacoes")


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cliente_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    unidade_id: Mapped[int] = mapped_column(Integer, ForeignKey("unidades.id"))
    canal_pedido: Mapped[CanalPedido] = mapped_column(SAEnum(CanalPedido))
    status: Mapped[StatusPedido] = mapped_column(SAEnum(StatusPedido), default=StatusPedido.AGUARDANDO_PAGAMENTO)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    desconto: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    cliente: Mapped["Usuario"] = relationship("Usuario", back_populates="pedidos")
    unidade: Mapped["Unidade"] = relationship("Unidade", back_populates="pedidos")
    itens: Mapped[list["ItemPedido"]] = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")
    pagamentos: Mapped[list["Pagamento"]] = relationship("Pagamento", back_populates="pedido")
    historico_status: Mapped[list["HistoricoStatusPedido"]] = relationship("HistoricoStatusPedido", back_populates="pedido")


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(Integer, ForeignKey("pedidos.id"))
    produto_id: Mapped[int] = mapped_column(Integer, ForeignKey("produtos.id"))
    quantidade: Mapped[int] = mapped_column(Integer)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="itens")
    produto: Mapped["Produto"] = relationship("Produto")


class Pagamento(Base):
    __tablename__ = "pagamentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(Integer, ForeignKey("pedidos.id"))
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[StatusPagamento] = mapped_column(SAEnum(StatusPagamento), default=StatusPagamento.PENDENTE)
    numero_tentativa: Mapped[int] = mapped_column(Integer, default=1)
    referencia_gateway: Mapped[str | None] = mapped_column(String(100), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("pedido_id", "numero_tentativa"),)

    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="pagamentos")


class HistoricoStatusPedido(Base):
    __tablename__ = "historico_status_pedido"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(Integer, ForeignKey("pedidos.id"))
    status_anterior: Mapped[str | None] = mapped_column(String(40), nullable=True)
    novo_status: Mapped[str] = mapped_column(String(40))
    motivo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="historico_status")
