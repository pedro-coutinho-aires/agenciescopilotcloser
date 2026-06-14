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
| Backend | Python 3.11+, FastAPI, Pydantic |
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui |
| LLM | Anthropic Claude (primario), OpenAI (fallback opcional) |
| Templates | Jinja2 (.j2) |

## Pre-requisitos

- Python 3.11+
- Node.js 20+
- Chave API da Anthropic (obrigatoria)
- Chave API da OpenAI (opcional, fallback)

## Setup

### 1. Clone e entre no diretorio

```bash
cd re_copilot
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Configurar variaveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` e adicione sua chave:

```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...  # opcional
```

### 4. Frontend

```bash
cd ../frontend
npm install
```

## Rodando

### Opcao 1: Script (mais facil)

```bash
# Edite backend/.env com sua ANTHROPIC_API_KEY, depois:
./start.sh
```

Um comando. Sobe backend + frontend juntos.

### Opcao 2: Docker Compose

```bash
# Edite backend/.env com sua ANTHROPIC_API_KEY, depois:
docker compose up --build
```

### Opcao 3: Manual (dois terminais)

**Terminal 1 — Backend (porta 8000):**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend (porta 3000):**
```bash
cd frontend
npm run dev
```

### Acesse

- App: **http://localhost:3000**
- API docs: **http://localhost:8000/docs**

## Demo Flow

1. A pagina carrega com um chat mostrando conversa com o lead
2. O lead diz "Quero fechar" — aparece um banner azul
3. Clique em **"Abrir Lais Close"** — o painel lateral abre
4. **Aba Documentos**: Checklist com 6 itens, vincule anexos do chat
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
re_copilot/
├── backend/
│   ├── main.py                 # FastAPI app + CORS
│   ├── models.py               # Modelos Pydantic
│   ├── routes/
│   │   ├── deal.py             # CRUD de deals
│   │   ├── generate.py         # Geracao de proposta/contrato/mensagem/resumo
│   │   └── chat.py             # Simulacao de lead
│   ├── services/
│   │   ├── llm_service.py      # Claude + OpenAI fallback
│   │   ├── template_engine.py  # Jinja2 + LLM enhancement
│   │   └── document_classifier.py
│   ├── templates/              # Templates Jinja2
│   └── data/mock_data.py       # Dados mockados
├── frontend/
│   ├── src/app/page.tsx        # Pagina principal
│   ├── src/components/         # Componentes React
│   ├── src/lib/api.ts          # Cliente API
│   └── src/types/index.ts      # Tipos TypeScript
```

## API Reference

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/api/mock-data` | Dados mockados |
| POST | `/api/deal` | Criar deal |
| GET | `/api/deal/{id}` | Buscar deal |
| PATCH | `/api/deal/{id}/link-attachment` | Vincular anexo |
| PATCH | `/api/deal/{id}/update-doc-status` | Atualizar status doc |
| POST | `/api/generate/proposal` | Gerar proposta |
| POST | `/api/generate/contract` | Gerar minuta |
| POST | `/api/generate/message` | Gerar mensagem |
| POST | `/api/generate/summary` | Gerar resumo |
| POST | `/api/chat/simulate` | Simular lead |

## Limitacoes (MVP)

- Sem autenticacao
- Sem banco de dados (estado em memoria, reseta ao reiniciar)
- Sem upload real de arquivos (anexos mockados)
- Sem integracao com WhatsApp/CRM
- Contratos sao minutas preliminares — sempre requerem revisao humana

---

Feito para o Lastro Hackathon 2026.
