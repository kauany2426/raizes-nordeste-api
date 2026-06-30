# Raízes do Nordeste — API

Backend da rede de lanchonetes **Raízes do Nordeste**, desenvolvido com **FastAPI** e **PostgreSQL** como projeto multidisciplinar do curso de Análise e Desenvolvimento de Sistemas — UNINTER 2026.

---

## Tecnologias

- Python 3.13
- FastAPI 0.115
- SQLAlchemy 2.0 (ORM)
- PostgreSQL
- JWT (access token 15min + refresh token 7 dias)
- Passlib + bcrypt (hash de senhas)

---

## Pré-requisitos

- Python 3.10 ou superior instalado
- PostgreSQL instalado e rodando
- Git (opcional)

---

## Instalação

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd raizes-nordeste-api
```

### 2. Crie o ambiente virtual e instale as dependências

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure o banco de dados

Crie o banco no PostgreSQL (substitua `seu_usuario` e `sua_senha` pelas suas credenciais):

```sql
-- conecta como superusuário (ex: postgres)
CREATE DATABASE raizes_nordeste;
CREATE USER seu_usuario WITH PASSWORD 'sua_senha';
GRANT ALL PRIVILEGES ON DATABASE raizes_nordeste TO seu_usuario;

-- necessário no PostgreSQL 15+
\c raizes_nordeste
GRANT ALL ON SCHEMA public TO seu_usuario;
```

### 4. Configure o arquivo .env

Copie o `.env.example` para `.env` e preencha com suas credenciais:

```bash
cp .env.example .env
```

Edite o `.env`:

```
DATABASE_URL=postgresql://seu_usuario:sua_senha@localhost:5432/raizes_nordeste

JWT_SECRET=troque-por-uma-chave-secreta-longa
JWT_REFRESH_SECRET=troque-por-outra-chave-secreta-longa
JWT_EXPIRES_MINUTES=15
JWT_REFRESH_EXPIRES_DAYS=7

PORT=8080
```

### 5. Popule o banco com dados iniciais

```bash
python seed.py
```

Usuários criados (todos com senha `senha123`):

| E-mail | Perfil |
|--------|--------|
| kauany.admin@raizes.com | ADMIN |
| pedro.gerente@raizes.com | GERENTE |
| ze.cozinha@raizes.com | COZINHA |
| fernanda.balcao@raizes.com | ATENDENTE |
| joao.cliente@gmail.com | CLIENTE |

### 6. Inicie o servidor

```bash
python main.py
```

A API estará disponível em `http://localhost:8080`

Documentação interativa: `http://localhost:8080/docs`

---

## Rotas principais

### Autenticação
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/auth/registro` | Cadastrar novo usuário |
| POST | `/auth/login` | Fazer login e obter tokens |
| POST | `/auth/refresh` | Renovar access token |
| POST | `/auth/logout` | Encerrar sessão |
| GET | `/auth/me` | Dados do usuário logado |

### Usuários
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/usuarios` | Listar usuários (ADMIN/GERENTE) |
| GET | `/usuarios/{id}` | Buscar usuário por ID |
| DELETE | `/usuarios/{id}` | Remover usuário (ADMIN) |

### Unidades
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/unidades` | Listar unidades |
| POST | `/unidades` | Criar unidade (ADMIN) |
| GET | `/unidades/{id}` | Buscar unidade |
| PUT | `/unidades/{id}` | Atualizar unidade (ADMIN/GERENTE) |

### Produtos
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/produtos` | Listar produtos |
| POST | `/produtos` | Criar produto (ADMIN) |
| PUT | `/produtos/{id}` | Atualizar produto (ADMIN) |
| POST | `/produtos/{id}/ativar` | Ativar produto |
| POST | `/produtos/{id}/desativar` | Desativar produto |

### Estoque e Cardápio
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/unidades/{id}/cardapio` | Ver cardápio da unidade |
| POST | `/unidades/{id}/cardapio` | Adicionar produto ao cardápio |
| PATCH | `/unidades/{id}/cardapio/{produto_id}` | Atualizar preço/disponibilidade |
| POST | `/unidades/{id}/estoque` | Registrar movimentação de estoque |
| GET | `/unidades/{id}/estoque` | Histórico de movimentações |

### Pedidos
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/pedidos` | Criar pedido |
| GET | `/pedidos` | Listar pedidos |
| GET | `/pedidos/{id}` | Buscar pedido |
| PATCH | `/pedidos/{id}/status` | Atualizar status |
| POST | `/pedidos/{id}/cancelar` | Cancelar pedido |

### Pagamentos
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/pagamentos/{pedido_id}/processar` | Processar pagamento |
| POST | `/pagamentos/{pedido_id}/nova-tentativa` | Nova tentativa de pagamento |
| GET | `/pagamentos/{pedido_id}` | Histórico de pagamentos |

---

## Perfis de acesso

| Perfil | Descrição |
|--------|-----------|
| ADMIN | Acesso total ao sistema |
| GERENTE | Gerencia unidades e pedidos |
| COZINHA | Atualiza status dos pedidos |
| ATENDENTE | Cria e gerencia pedidos no balcão |
| CLIENTE | Faz pedidos e acompanha status |

---

## Funcionalidades

- **Autenticação JWT** com access token (15 min) e refresh token (7 dias)
- **Controle de estoque** automático ao criar/cancelar pedidos
- **Programa de fidelidade**: 1 ponto por R$ 1,00 gasto; 100 pontos = R$ 1,00 de desconto (máximo 50% do subtotal)
- **Gateway de pagamento mock**: 80% de aprovação na 1ª tentativa, 95% nas seguintes
- **Histórico de status** de cada pedido
- **LGPD**: consentimento obrigatório no cadastro
