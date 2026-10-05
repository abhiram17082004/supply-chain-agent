from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from src.api.routes.chat import router
from src.security.limiter import limiter

load_dotenv()

app = FastAPI(
    title="Supply Chain Intelligence Agent",
    description="AI agent — LangGraph + Groq + LangChain",
    version="2.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
