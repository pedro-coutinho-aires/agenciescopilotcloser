# Lais Close — Copiloto de Fechamento para Locacao

> Quando o lead diz "quero fechar", o corretor ainda precisa sair do chat, procurar documentos, montar proposta, acionar administrativo e acompanhar pendencias manualmente. O **Lais Close** transforma esse momento em uma esteira guiada dentro da propria conversa.

## O que e

O Lais Close e um copiloto de fechamento para locacao imobiliaria. Ele funciona como um painel lateral acoplado ao chat com o lead e permite ao corretor:

1. **Acompanhar documentos** — Checklist automatico, vinculacao de anexos do chat
2. **Gerar propostas** — Formulario pre-preenchido + geracao com IA
3. **Gerar minutas contratuais** — Template + IA, com campos pendentes destacados
4. **Gerar mensagens** — Mensagens prontas para WhatsApp (pedir documentos, confirmar proposta, etc.)
5. **Resumir o fechamento** — Resumo completo com proxima acao sugerida
6. **Simular o lead** — Chat com IA simulando o lead para testes/demo

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL |
| Frontend | Next.js 16, TypeScript, Tailwind CSS, shadcn/ui |
| LLM | Anthropic Claude (primario), OpenAI (fallback opcional) |
| Templates | Jinja2 (.j2) |

## Pre-requisitos

- **Docker** e **Docker Compose** (recomendado — sobe tudo com um comando)
- **OU**, para rodar localmente sem Docker:
  - Python 3.11+
  - Node.js 20+
  - PostgreSQL 16+ (porta `5432`)
- Chave API da **Anthropic** (obrigatoria)
- Chave API da **OpenAI** (opcional, fallback)
- Chave **Clicksign** (opcional, assinatura digital)

## Quick start (recomendado)

### 1. Clone o repositorio

```bash
git clone git@github.com:pedro-coutinho-aires/laiscloser.git
cd laiscloser
```

### 2. Configure as variaveis de ambiente

```bash
cp backend/.env.example backend/.env
```

Edite `backend/.env` e preencha pelo menos a chave da Anthropic:

```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...          # opcional
CLICKSIGN_API_KEY=...          # opcional
DATABASE_URL=postgresql+asyncpg://lais:lais@localhost:5432/lais_close
```

> No Docker Compose, o `DATABASE_URL` do backend e sobrescrito automaticamente para apontar ao container Postgres.

### 3. Suba o projeto

```bash
docker compose up --build
```

Aguarde os tres servicos ficarem prontos: **postgres**, **backend** e **frontend**.

### 4. Acesse

| Servico | URL |
|---------|-----|
| App | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |

Para parar:

```bash
docker compose down
```

Para parar e apagar os dados do banco:

```bash
docker compose down -v
```

---

## Rodando sem Docker

Use esta opcao se preferir executar backend e frontend direto na maquina.

### 1. Clone e configure o `.env`

```bash
git clone git@github.com:pedro-coutinho-aires/laiscloser.git
cd laiscloser
cp backend/.env.example backend/.env
# Edite backend/.env e adicione ANTHROPIC_API_KEY
```

### 2. Suba o PostgreSQL

O backend precisa de um Postgres acessivel em `localhost:5432` com usuario/senha `lais`/`lais` e banco `lais_close` (valores padrao do `.env.example`).

**Opcao A — so o banco via Docker (mais simples):**

```bash
docker compose up postgres -d
```

**Opcao B — Postgres instalado localmente:**

```bash
createdb lais_close
# ou ajuste DATABASE_URL em backend/.env
```

### 3. Escolha como subir backend + frontend

#### Opcao A: Script unico (mais facil)

Na raiz do projeto:

```bash
chmod +x start.sh   # apenas na primeira vez
./start.sh
```

O script:
- cria o venv Python e instala dependencias do backend
- instala dependencias do frontend (`npm install`)
- sobe backend na porta **8000** e frontend na porta **3000**

Pressione `Ctrl+C` para encerrar os dois servicos.

#### Opcao B: Dois terminais (controle manual)

**Terminal 1 — Backend:**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm install
npm run dev
```

### 4. Acesse

- App: **http://localhost:3000**
- API docs: **http://localhost:8000/docs**

---

## Verificando se esta funcionando

1. Abra http://localhost:3000 — a pagina deve carregar com o chat do lead.
2. Abra http://localhost:8000/api/health — deve retornar `{"status":"ok"}`.
3. Na primeira subida, o backend cria as tabelas e popula dados de demo automaticamente.

Se o backend falhar ao iniciar, confira:
- Postgres rodando e acessivel na porta `5432`
- `ANTHROPIC_API_KEY` definida em `backend/.env`
- Portas `3000` e `8000` livres

---

## Demo Flow

1. A pagina carrega com um chat mostrando conversa com o lead
2. O lead diz "Quero fechar" — aparece um banner azul
3. Clique em **"Abrir Lais Close"** — o painel lateral abre
4. **Aba Documentos**: Checklist com itens, vincule anexos do chat
5. **Aba Proposta**: Preencha valores, clique "Gerar Proposta"
6. **Aba Contrato**: Clique "Gerar Minuta" — campos pendentes em destaque
7. **Aba Resumo**: Clique "Gerar Resumo" — resumo completo com proxima acao
8. Use os botoes "Gerar mensagem" para criar mensagens prontas para WhatsApp
9. Digite no chat e o lead responde automaticamente (IA)

## Templates Customizaveis

O sistema usa templates Jinja2 para gerar propostas e contratos. Para adicionar um novo template:

1. Crie um arquivo `.j2` em `backend/templates/`
2. Use variaveis Jinja2 (ex: `{{ lead_name }}`, `{{ rent }}`)
3. O template fica disponivel automaticamente nos endpoints de geracao

Templates disponiveis:
- `proposal_default.j2` — Proposta de locacao
- `contract_default.j2` — Minuta de contrato
- `messages.j2` — Templates de mensagens para o lead

## Arquitetura

```
laiscloser/
├── backend/
│   ├── main.py                 # FastAPI app + CORS
│   ├── models.py               # Modelos Pydantic
│   ├── db/                     # SQLAlchemy + seed
│   ├── routes/
│   │   ├── deal.py             # CRUD de deals
│   │   ├── generate.py         # Geracao de proposta/contrato/mensagem/resumo
│   │   ├── documents.py        # Upload e analise de documentos
│   │   ├── templates.py        # Templates customizados
│   │   └── chat.py             # Simulacao de lead
│   ├── services/
│   │   ├── llm_service.py      # Claude + OpenAI fallback
│   │   ├── template_engine.py  # Jinja2 + LLM enhancement
│   │   └── document_classifier.py
│   ├── templates/              # Templates Jinja2
│   └── uploads/                # Arquivos enviados
├── frontend/
│   ├── src/app/page.tsx        # Pagina principal
│   ├── src/components/         # Componentes React
│   ├── src/lib/api.ts          # Cliente API
│   └── src/types/index.ts      # Tipos TypeScript
├── docker-compose.yml          # Postgres + backend + frontend
└── start.sh                    # Atalho para dev local
```

## API Reference

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/api/health` | Health check |
| GET | `/api/mock-data` | Dados mockados |
| POST | `/api/deal` | Criar deal |
| GET | `/api/deal/{id}` | Buscar deal |
| PATCH | `/api/deal/{id}/link-attachment` | Vincular anexo |
| PATCH | `/api/deal/{id}/update-doc-status` | Atualizar status doc |
| POST | `/api/documents/process` | Processar documento |
| POST | `/api/generate/proposal` | Gerar proposta |
| POST | `/api/generate/contract` | Gerar minuta |
| POST | `/api/generate/message` | Gerar mensagem |
| POST | `/api/generate/summary` | Gerar resumo |
| POST | `/api/chat/simulate` | Simular lead |

Documentacao interativa completa: http://localhost:8000/docs

## Limitacoes (MVP)

- Sem autenticacao
- Sem integracao real com WhatsApp/CRM
- Contratos sao minutas preliminares — sempre requerem revisao humana
- Clicksign usa sandbox por padrao

---

Feito para o Lastro Hackathon 2026.
