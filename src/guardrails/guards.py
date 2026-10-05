from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser


# ── Input validation runnable ─────────────────────────────────
def _validate(query: str) -> str:
    if not query or not query.strip():
        raise ValueError("Please type a message.")
    if len(query) > 1500:
        raise ValueError("Query too long. Max 1500 characters.")
    return query.strip()

input_validator = RunnableLambda(_validate)

# ── Output parser ─────────────────────────────────────────────
_output_parser = StrOutputParser()


# ── Public interface (keeps same API as before) ───────────────
class _Result:
    def __init__(self, is_safe, sanitized="", reason=""):
        self.is_safe   = is_safe
        self.sanitized = sanitized
        self.reason    = reason


def check_input(query: str) -> _Result:
    try:
        clean = input_validator.invoke(query)
        return _Result(is_safe=True, sanitized=clean)
    except ValueError as e:
        return _Result(is_safe=False, reason=str(e))


def check_output(text: str, tool_calls_used: list) -> dict:
    parsed = _output_parser.invoke(text)
    return {"text": parsed, "issues": []}
