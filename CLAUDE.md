# Lais Close — Copiloto de Fechamento para Locacao

## Project Overview

Lais Close is a closing copilot sidebar for real estate rentals. It sits inside a chat interface and helps brokers manage the closing process: document checklists, proposal generation, contract drafts, lead communication, and closing summaries.

**Stack**: Python (FastAPI + Pydantic) backend + Next.js (TypeScript + Tailwind + shadcn/ui) frontend.

## Architecture

```
re_copilot/
├── backend/              # Python FastAPI server (port 8000)
│   ├── main.py           # App entry, CORS, router includes
│   ├── models.py         # Pydantic models for all entities
│   ├── routes/           # API endpoints (deal, generate, chat)
│   ├── services/         # LLM service, template engine, doc classifier
│   ├── templates/        # Jinja2 templates (.j2 files)
│   └── data/             # Mock data (leads, properties, messages)
├── frontend/             # Next.js app (port 3000)
│   ├── src/app/          # App router pages
│   ├── src/components/   # React components (Chat, ClosePanel, tabs)
│   ├── src/lib/          # API client
│   └── src/types/        # TypeScript types
```

### Key Design Decisions

- **Template system**: Jinja2 templates in `backend/templates/`. Drop a new `.j2` file and it's immediately available. Base render is deterministic, LLM refines/customizes.
- **LLM**: Claude (Anthropic) primary, OpenAI optional fallback. Used for proposal/contract enhancement, lead simulation, message generation, and summary creation.
- **State**: In-memory dict on backend (no database). Frontend fetches via API.

## Development

### Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your ANTHROPIC_API_KEY

# Frontend
cd frontend
npm install
```

### Running the project

```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open http://localhost:3000

### API Endpoints

- `GET /api/mock-data` — Get mock lead, property, messages
- `POST /api/deal` — Create a deal
- `GET /api/deal/{id}` — Get deal state
- `PATCH /api/deal/{id}/link-attachment` — Link chat attachment to document
- `PATCH /api/deal/{id}/update-doc-status` — Update document status
- `POST /api/generate/proposal` — Generate proposal (template + LLM)
- `POST /api/generate/contract` — Generate contract draft (template + LLM)
- `POST /api/generate/message` — Generate lead-facing message (LLM)
- `POST /api/generate/summary` — Generate closing summary (LLM)
- `POST /api/chat/simulate` — Simulate lead response (LLM)

### Adding Custom Templates

Drop a `.j2` file in `backend/templates/`. Use Jinja2 syntax with context variables. See existing templates for reference.

## Notes

- MVP for hackathon — no auth, no database, no real file uploads
- State resets on backend restart
- Contract drafts are preliminary and always include human review warnings
