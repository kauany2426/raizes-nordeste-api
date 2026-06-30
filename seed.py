"""
Script para popular o banco com dados iniciais para teste.
Execute com: python seed.py
"""

from database import SessionLocal, Base, engine
from models import Usuario, Unidade, Produto, ItemCardapio, MovimentacaoEstoque
from security import hash_senha
from enums import Perfil, TipoMovimentacao

# cria as tabelas se não existirem
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # verifica se já tem dados no banco para não duplicar
    if db.query(Usuario).count() > 0:
        print("Banco já possui dados. Seed cancelado.")
        db.close()
        exit()

    print("Inserindo dados iniciais...")

    # --- usuários ---
    admin = Usuario(
        nome="Kauany Administradora",
        email="kauany.admin@raizes.com",
        senha_hash=hash_senha("senha123"),
        perfil=Perfil.ADMIN,
        consentimento_lgpd=True
    )

    gerente = Usuario(
        nome="Pedro Henrique",
        email="pedro.gerente@raizes.com",
        senha_hash=hash_senha("senha123"),
        perfil=Perfil.GERENTE,
        consentimento_lgpd=True
    )

    cozinheiro = Usuario(
        nome="Seu Zé da Cozinha",
        email="ze.cozinha@raizes.com",
        senha_hash=hash_senha("senha123"),
        perfil=Perfil.COZINHA,
        consentimento_lgpd=True
    )

    atendente = Usuario(
        nome="Fernanda Atendente",
        email="fernanda.balcao@raizes.com",
        senha_hash=hash_senha("senha123"),
        perfil=Perfil.ATENDENTE,
        consentimento_lgpd=True
    )

    cliente1 = Usuario(
        nome="João Oliveira",
        email="joao.cliente@gmail.com",
        senha_hash=hash_senha("senha123"),
        perfil=Perfil.CLIENTE,
        consentimento_lgpd=True
    )

    db.add_all([admin, gerente, cozinheiro, atendente, cliente1])
    db.flush()

    # --- unidades ---
    unidade1 = Unidade(
        nome="Raízes do Nordeste - Recife Boa Viagem",
        endereco="Av. Conselheiro Aguiar, 1200 - Boa Viagem, Recife - PE"
    )
    unidade2 = Unidade(
        nome="Raízes do Nordeste - João Pessoa Centro",
        endereco="Rua Duque de Caxias, 350 - Centro, João Pessoa - PB"
    )

    db.add_all([unidade1, unidade2])
    db.flush()

    # --- produtos ---
    cuscuz = Produto(
        nome="Cuscuz com Queijo Coalho",
        categoria="Café da Manhã",
        descricao="Cuscuz de milho quentinho servido com queijo coalho grelhado"
    )
    buchada = Produto(
        nome="Buchada de Bode",
        categoria="Prato Principal",
        descricao="Prato típico nordestino com buchada temperada na brasa"
    )
    peixada = Produto(
        nome="Peixada Nordestina",
        categoria="Prato Principal",
        descricao="Peixe cozido com legumes e pirão"
    )
    suco_umbu = Produto(
        nome="Suco de Umbu",
        categoria="Bebida",
        descricao="Suco natural de umbu gelado, fruta típica do sertão"
    )
    cafe = Produto(
        nome="Café com Leite de Coalho",
        categoria="Bebida",
        descricao="Café coado com leite de coalho, sabor único nordestino"
    )
    cocada = Produto(
        nome="Cocada de Forno",
        categoria="Sobremesa",
        descricao="Cocada assada com coco fresco e leite condensado"
    )

    db.add_all([cuscuz, buchada, peixada, suco_umbu, cafe, cocada])
    db.flush()

    # --- cardápio da unidade Recife ---
    itens_recife = [
        ItemCardapio(produto_id=cuscuz.id, unidade_id=unidade1.id, preco_local=12.50, quantidade_atual=60),
        ItemCardapio(produto_id=buchada.id, unidade_id=unidade1.id, preco_local=38.00, quantidade_atual=20),
        ItemCardapio(produto_id=peixada.id, unidade_id=unidade1.id, preco_local=45.00, quantidade_atual=15),
        ItemCardapio(produto_id=suco_umbu.id, unidade_id=unidade1.id, preco_local=9.00, quantidade_atual=50),
        ItemCardapio(produto_id=cafe.id, unidade_id=unidade1.id, preco_local=7.00, quantidade_atual=80),
        ItemCardapio(produto_id=cocada.id, unidade_id=unidade1.id, preco_local=6.50, quantidade_atual=40),
    ]
    db.add_all(itens_recife)

    # --- cardápio da unidade João Pessoa ---
    itens_jp = [
        ItemCardapio(produto_id=cuscuz.id, unidade_id=unidade2.id, preco_local=11.00, quantidade_atual=50),
        ItemCardapio(produto_id=peixada.id, unidade_id=unidade2.id, preco_local=43.00, quantidade_atual=10),
        ItemCardapio(produto_id=suco_umbu.id, unidade_id=unidade2.id, preco_local=8.50, quantidade_atual=45),
        ItemCardapio(produto_id=cafe.id, unidade_id=unidade2.id, preco_local=6.50, quantidade_atual=70),
        ItemCardapio(produto_id=cocada.id, unidade_id=unidade2.id, preco_local=6.00, quantidade_atual=30),
    ]
    db.add_all(itens_jp)

    # registra as movimentações de entrada do estoque inicial
    movs_recife = [
        MovimentacaoEstoque(produto_id=cuscuz.id, unidade_id=unidade1.id, tipo=TipoMovimentacao.ENTRADA, quantidade=60, motivo="Estoque inicial", usuario_id=admin.id),
        MovimentacaoEstoque(produto_id=buchada.id, unidade_id=unidade1.id, tipo=TipoMovimentacao.ENTRADA, quantidade=20, motivo="Estoque inicial", usuario_id=admin.id),
        MovimentacaoEstoque(produto_id=peixada.id, unidade_id=unidade1.id, tipo=TipoMovimentacao.ENTRADA, quantidade=15, motivo="Estoque inicial", usuario_id=admin.id),
        MovimentacaoEstoque(produto_id=suco_umbu.id, unidade_id=unidade1.id, tipo=TipoMovimentacao.ENTRADA, quantidade=50, motivo="Estoque inicial", usuario_id=admin.id),
        MovimentacaoEstoque(produto_id=cafe.id, unidade_id=unidade1.id, tipo=TipoMovimentacao.ENTRADA, quantidade=80, motivo="Estoque inicial", usuario_id=admin.id),
        MovimentacaoEstoque(produto_id=cocada.id, unidade_id=unidade1.id, tipo=TipoMovimentacao.ENTRADA, quantidade=40, motivo="Estoque inicial", usuario_id=admin.id),
    ]
    movs_jp = [
        MovimentacaoEstoque(produto_id=cuscuz.id, unidade_id=unidade2.id, tipo=TipoMovimentacao.ENTRADA, quantidade=50, motivo="Estoque inicial", usuario_id=admin.id),
        MovimentacaoEstoque(produto_id=peixada.id, unidade_id=unidade2.id, tipo=TipoMovimentacao.ENTRADA, quantidade=10, motivo="Estoque inicial", usuario_id=admin.id),
        MovimentacaoEstoque(produto_id=suco_umbu.id, unidade_id=unidade2.id, tipo=TipoMovimentacao.ENTRADA, quantidade=45, motivo="Estoque inicial", usuario_id=admin.id),
        MovimentacaoEstoque(produto_id=cafe.id, unidade_id=unidade2.id, tipo=TipoMovimentacao.ENTRADA, quantidade=70, motivo="Estoque inicial", usuario_id=admin.id),
        MovimentacaoEstoque(produto_id=cocada.id, unidade_id=unidade2.id, tipo=TipoMovimentacao.ENTRADA, quantidade=30, motivo="Estoque inicial", usuario_id=admin.id),
    ]
    db.add_all(movs_recife + movs_jp)

    db.commit()
    print("Seed concluído com sucesso!")
    print("\nUsuários criados (todos com senha: senha123):")
    print("  kauany.admin@raizes.com     (ADMIN)")
    print("  pedro.gerente@raizes.com    (GERENTE)")
    print("  ze.cozinha@raizes.com       (COZINHA)")
    print("  fernanda.balcao@raizes.com  (ATENDENTE)")
    print("  joao.cliente@gmail.com      (CLIENTE)")

except Exception as e:
    db.rollback()
    print(f"Erro ao executar o seed: {e}")
finally:
    db.close()
