from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from db.engine import engine, AsyncSessionLocal
from db.base import Base
from db.seed import seed_db

from routes.deal import router as deal_router
from routes.generate import router as generate_router
from routes.chat import router as chat_router
from routes.documents import router as documents_router
from routes.templates import router as templates_router
from routes.guidelines import router as guidelines_router

UPLOADS_DIR = Path(__file__).parent / "uploads"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure uploads directory exists
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Startup: create tables and seed if empty
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_db(session)

    yield

    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(title="Agencies Copilot Closer API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(deal_router, prefix="/api")
app.include_router(generate_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(templates_router, prefix="/api")
app.include_router(guidelines_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/mock-docs/{filename}")
def serve_mock_doc(filename: str):
    """Serve mock lead documents for the simulated lead to 'send'."""
    from fastapi.responses import FileResponse

    mock_dir = Path(__file__).parent / "data" / "lead_mocked_docs"
    file_path = mock_dir / filename
    if not file_path.exists():
        from fastapi import HTTPException
        raise HTTPException(404, f"File {filename} not found")
    return FileResponse(file_path)
