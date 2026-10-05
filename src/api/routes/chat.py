import os
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from src.guardrails.guards import check_input
from src.agent.orchestrator import run_agent
from src.security.limiter import limiter

load_dotenv()
router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    answer: str
    tools_used: list[str]
    warnings: list[str]
    session_id: str


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
def chat(request: Request, req: ChatRequest, x_api_key: str = Header(...)):
    if x_api_key != os.getenv("AGENT_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")

    guard = check_input(req.query)
    if not guard.is_safe:
        raise HTTPException(status_code=400, detail=guard.reason)

    result = run_agent(guard.sanitized, req.session_id)

    return ChatResponse(
        answer=result["answer"],
        tools_used=result.get("tool_calls", []),
        warnings=result.get("warnings", []),
        session_id=req.session_id
    )
