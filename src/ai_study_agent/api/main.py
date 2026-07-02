"""FastAPI application factory and default app instance."""

from __future__ import annotations

from collections.abc import Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_study_agent.api.errors import register_exception_handlers
from ai_study_agent.api.routers import agents, cards, chat, health, knowledge, rag

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def create_app(cors_origins: Sequence[str] = DEFAULT_CORS_ORIGINS) -> FastAPI:
    app = FastAPI(
        title="AI Study Agent API",
        version="0.1.0",
        description="Backend API for Chat, RAG, QA cards, and Agent learning workflows.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(health.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    app.include_router(knowledge.router, prefix="/api")
    app.include_router(rag.router, prefix="/api")
    app.include_router(cards.router, prefix="/api")
    app.include_router(agents.router, prefix="/api")
    return app


app = create_app()
