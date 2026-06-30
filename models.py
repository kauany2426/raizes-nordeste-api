from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from enums import Perfil, CanalPedido, StatusPedido, StatusPagamento, TipoMovimentacao


# tabela de usuários do sistema
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(Enum(Perfil), default=Perfil.CLIENTE)
    consentimento_lgpd = Column(Boolean, default=False)
    pontos_fidelidade = Column(Integer, default=0)
    refresh_token_hash = Column(String(255), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pedidos = relationship("Pedido", back_populates="cliente")
    movimentacoes = relationship("MovimentacaoEstoque", back_populates="usuario")


# tabela de unidades da rede (cada lanchonete é uma unidade)
class Unidade(Base):
    __tablename__ = "unidades"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    endereco = Column(String(300), nullable=False)
    ativa = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    itens_cardapio = relationship("ItemCardapio", back_populates="unidade")
    pedidos = relationship("Pedido", back_populates="unidade")
    movimentacoes = relationship("MovimentacaoEstoque", back_populates="unidade")


# tabela de produtos (cadastro geral, sem preço - preço é por unidade)
class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    descricao = Column(Text, nullable=True)
    categoria = Column(String(80), nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    itens_cardapio = relationship("ItemCardapio", back_populates="produto")
    movimentacoes = relationship("MovimentacaoEstoque", back_populates="produto")


# cardápio: produto + unidade com preço e estoque próprios de cada unidade
class ItemCardapio(Base):
    __tablename__ = "itens_cardapio"

    produto_id = Column(Integer, ForeignKey("produtos.id"), primary_key=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), primary_key=True)
    preco_local = Column(Numeric(10, 2), nullable=False)
    quantidade_atual = Column(Integer, default=0)
    disponivel = Column(Boolean, default=True)

    produto = relationship("Produto", back_populates="itens_cardapio")
    unidade = relationship("Unidade", back_populates="itens_cardapio")


# registra todas as entradas e saídas de estoque
class MovimentacaoEstoque(Base):
    __tablename__ = "movimentacoes_estoque"

    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=False)
    tipo = Column(Enum(TipoMovimentacao), nullable=False)
    quantidade = Column(Integer, nullable=False)
    motivo = Column(String(255), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    produto = relationship("Produto", back_populates="movimentacoes")
    unidade = relationship("Unidade", back_populates="movimentacoes")
    usuario = relationship("Usuario", back_populates="movimentacoes")


# pedido feito por um cliente em uma unidade
class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=False)
    canal_pedido = Column(Enum(CanalPedido), nullable=False)
    status = Column(Enum(StatusPedido), default=StatusPedido.AGUARDANDO_PAGAMENTO)
    subtotal = Column(Numeric(10, 2), nullable=False)
    desconto = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cliente = relationship("Usuario", back_populates="pedidos")
    unidade = relationship("Unidade", back_populates="pedidos")
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")
    pagamentos = relationship("Pagamento", back_populates="pedido")
    historico = relationship("HistoricoStatusPedido", back_populates="pedido")


# cada linha de produto dentro de um pedido
class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)

    pedido = relationship("Pedido", back_populates="itens")
    produto = relationship("Produto")


# pagamento associado a um pedido (mock, não é real)
class Pagamento(Base):
    __tablename__ = "pagamentos"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(StatusPagamento), default=StatusPagamento.PENDENTE)
    numero_tentativa = Column(Integer, default=1)
    referencia_gateway = Column(String(100), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("pedido_id", "numero_tentativa"),)

    pedido = relationship("Pedido", back_populates="pagamentos")


# guarda o histórico de mudanças de status do pedido
class HistoricoStatusPedido(Base):
    __tablename__ = "historico_status_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    status_anterior = Column(String(40), nullable=True)
    novo_status = Column(String(40), nullable=False)
    motivo = Column(String(255), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    pedido = relationship("Pedido", back_populates="historico")
