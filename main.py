"""
Google ADK AI Agent  ·  FastAPI  ·  Vertex AI Gemini 2.5 Flash
Auth: Application Default Credentials (ADC)
  - Local dev  → GOOGLE_APPLICATION_CREDENTIALS key file
  - Cloud Run  → Attached service account (automatic)
  - GKE        → Workload Identity or node SA (automatic)
"""

# main.py  — add at the very top, before all other imports
from dotenv import load_dotenv
load_dotenv()   # reads .env file automatically

import os
import uuid
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import google.auth
import vertexai
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Configuration  (all overridable via environment variables)
# ─────────────────────────────────────────────────────────────
MODEL    = os.getenv("MODEL",                  "gemini-2.5-flash")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION",  "us-central1")
APP_NAME = os.getenv("ADK_APP_NAME",           "adk-fastapi-agent")

# PROJECT_ID is optional here — google.auth.default() can detect it automatically
# when running on Cloud Run / GKE.  Set it explicitly for local dev.
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")


# Replace init_vertex_ai() function with this:
def init_vertex_ai() -> None:
    """
    Validate required env vars are present.
    ADK routes to Vertex AI automatically when GOOGLE_GENAI_USE_VERTEXAI=true.
    Credentials are picked up by google.auth.default() automatically.
    """
    project  = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    if not project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT environment variable is not set.")

    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower()
    if use_vertex != "true":
        raise RuntimeError(
            "GOOGLE_GENAI_USE_VERTEXAI is not set to 'true'. "
            "ADK will route to AI Studio instead of Vertex AI."
        )

    # Verify credentials are accessible
    credentials, detected_project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    log.info(
        "✅  Vertex AI ready | project=%s | location=%s | model=%s",
        project, location, MODEL
    )
# ─────────────────────────────────────────────────────────────
# ADK Agent
# ─────────────────────────────────────────────────────────────
def build_agent() -> Agent:
    return Agent(
        name="adk_level1_basic",
        model=MODEL,
        description="A helpful AI assistant powered by Gemini 2.5 Flash on Vertex AI.",
        instruction=(
            "You are a concise, knowledgeable assistant. "
            "Answer questions clearly and helpfully. "
            "If you are unsure about something, say so honestly."
        ),
    )


# ─────────────────────────────────────────────────────────────
# App-level shared state
# ─────────────────────────────────────────────────────────────
class AppState:
    runner:          Runner | None          = None
    session_service: InMemorySessionService | None = None


state = AppState()


# ─────────────────────────────────────────────────────────────
# FastAPI lifespan  (startup / shutdown)
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ── Startup ──────────────────────────────────────────────
    log.info("🚀  Starting up …")
    init_vertex_ai()

    agent                = build_agent()
    state.session_service = InMemorySessionService()
    state.runner         = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=state.session_service,
    )
    log.info("✅  ADK Runner ready")
    yield

    # ── Shutdown ─────────────────────────────────────────────
    log.info("👋  Shutting down")


# ─────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Google ADK Agent API",
    description=(
        "FastAPI wrapper around a Google ADK agent.\n\n"
        "**Model:** Gemini 2.5 Flash  |  **Auth:** ADC (Cloud Run / GKE / local)"
    ),
    version="2.0.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message:    str
    session_id: str | None = None   # omit → new session per request
    user_id:    str        = "default_user"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"message": "What is the capital of France?", "user_id": "alice"}
            ]
        }
    }


class ChatResponse(BaseModel):
    session_id: str
    user_id:    str
    reply:      str


class HealthResponse(BaseModel):
    status:  str
    model:   str
    app:     str
    project: str


# ─────────────────────────────────────────────────────────────
# Internal helper
# ─────────────────────────────────────────────────────────────
async def _ensure_session(session_id: str, user_id: str) -> None:
    """Create session if it doesn't exist yet."""
    existing = await state.session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if existing is None:
        await state.session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )


async def run_agent(session_id: str, user_id: str, message: str) -> str:
    """Send *message* to the runner and return the final text reply."""
    await _ensure_session(session_id, user_id)

    user_content = types.Content(
        role="user",
        parts=[types.Part(text=message)],
    )

    final_reply = ""
    async for event in state.runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_reply = "".join(
                p.text for p in event.content.parts if hasattr(p, "text")
            )

    return final_reply or "(no response)"


# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["Ops"])
async def health() -> HealthResponse:
    """Liveness / readiness probe — safe to call from Cloud Run & GKE."""
    _, detected_project = google.auth.default()
    return HealthResponse(
        status="ok",
        model=MODEL,
        app=APP_NAME,
        project=PROJECT_ID or detected_project or "unknown",
    )


@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Single-turn or multi-turn chat.

    - Omit `session_id` for a fresh stateless call.
    - Pass the same `session_id` across calls to maintain conversation history.
    """
    session_id = req.session_id or str(uuid.uuid4())
    log.info("chat  user=%s  session=%s  msg=%.80s", req.user_id, session_id, req.message)

    try:
        reply = await run_agent(session_id, req.user_id, req.message)
    except Exception as exc:
        log.exception("Agent error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(session_id=session_id, user_id=req.user_id, reply=reply)


@app.post("/chat/stream", tags=["Agent"])
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    """
    Streaming chat via Server-Sent Events (SSE).

    Each SSE event is JSON:
      `{"chunk": "…"}` during generation
      `{"session_id": "…"}` as first event
      `[DONE]` as final event
    """
    session_id = req.session_id or str(uuid.uuid4())
    log.info("stream user=%s  session=%s  msg=%.80s", req.user_id, session_id, req.message)

    await _ensure_session(session_id, req.user_id)

    user_content = types.Content(
        role="user",
        parts=[types.Part(text=req.message)],
    )

    async def event_generator():
        yield f'data: {{"session_id": "{session_id}"}}\n\n'
        try:
            async for event in state.runner.run_async(
                user_id=req.user_id,
                session_id=session_id,
                new_message=user_content,
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            # Escape newlines so SSE framing is not broken
                            chunk = part.text.replace("\\", "\\\\").replace("\n", "\\n")
                            yield f'data: {{"chunk": "{chunk}"}}\n\n'
        except Exception as exc:
            log.exception("Stream error")
            yield f'data: {{"error": "{exc}"}}\n\n'
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.delete("/session/{session_id}", tags=["Session"])
async def delete_session(
    session_id: str,
    user_id:    str = "default_user",
) -> dict:
    """Delete a conversation session and its history."""
    await state.session_service.delete_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    log.info("session deleted  user=%s  session=%s", user_id, session_id)
    return {"deleted": session_id, "user_id": user_id}


# ─────────────────────────────────────────────────────────────
# Local dev entry-point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)