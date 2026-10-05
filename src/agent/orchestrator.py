import os
import asyncio
import httpx
import urllib3
from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver        # LangGraph memory
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from src.tools.lc_tools import LANGCHAIN_TOOLS
from src.guardrails.guards import check_output

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOOL_NAMES = {t.name for t in LANGCHAIN_TOOLS}

# ── LLM ───────────────────────────────────────────────────────
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    http_client=httpx.Client(verify=False),
)
llm_with_tools = llm.bind_tools(LANGCHAIN_TOOLS)

SYSTEM_PROMPT = """You are a Supply Chain Intelligence Agent for DataCo Global.
You have access to real supply chain data: 180,000+ orders across 5 global markets.

MARKETS (with full names):
  LATAM        = Latin America
  Europe       = European region
  Pacific Asia = Asia-Pacific region
  USCA         = United States and Canada
  Africa       = African region
SHIPPING MODES: First Class, Second Class, Standard Class, Same Day
CUSTOMER SEGMENTS: Consumer, Corporate, Home Office
DELIVERY STATUSES: Late delivery, Advance shipping, Shipping on time, Shipping canceled

YOUR TOOLS:
1. search_knowledge_base — for market overviews, category profiles, shipping summaries
2. run_sql_query — for exact numbers, aggregations, filters, rankings (SELECT only)
3. get_delivery_risk_report — for ranking dimensions by delivery performance

HOW TO RESPOND:
- If asked "what is X" — first explain what X means in plain English, then give the data
- Always call a tool before stating any statistic or number
- For "which X has worst/best Y" use get_delivery_risk_report
- For "how many / total / average" use run_sql_query
- For "tell me about / summarize" use search_knowledge_base first
- Always mention which tool provided the data
- Format: percentages to 1 decimal, dollars to 2 decimals
- Decline questions unrelated to supply chain"""


# ── LangGraph State ───────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# ── Nodes ─────────────────────────────────────────────────────
def call_model(state: AgentState) -> dict:
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    return {"messages": [llm_with_tools.invoke(messages)]}


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    return "tools" if (hasattr(last, "tool_calls") and last.tool_calls) else END


# ── Build Graph with MemorySaver ──────────────────────────────
memory = MemorySaver()                          # LangGraph handles all session memory

graph_builder = StateGraph(AgentState)
graph_builder.add_node("agent", call_model)
graph_builder.add_node("tools", ToolNode(LANGCHAIN_TOOLS))
graph_builder.set_entry_point("agent")
graph_builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph_builder.add_edge("tools", "agent")

agent_graph = graph_builder.compile(checkpointer=memory)  # memory wired in here


# ── Streaming — uses LangGraph astream_events ─────────────────
def stream_agent(user_query: str, session_id: str = "default"):
    """
    Returns (text_generator, meta_dict).
    Uses LangGraph MemorySaver — no manual history needed, just session_id.
    Uses astream_events for token streaming + tool progress indicators.
    """
    config  = {"configurable": {"thread_id": session_id}}
    meta    = {"tool_calls": []}

    async def _async_gen():
        async for event in agent_graph.astream_events(
            {"messages": [HumanMessage(content=user_query)]},
            config=config,
            version="v2",
        ):
            kind = event["event"]

            # Stream LLM tokens as they generate
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield chunk.content

            # Show tool start indicator
            elif kind == "on_tool_start":
                name = event.get("name", "")
                if name in TOOL_NAMES and name not in meta["tool_calls"]:
                    meta["tool_calls"].append(name)

    def sync_generator():
        loop = asyncio.new_event_loop()
        agen = _async_gen()
        try:
            while True:
                try:
                    yield loop.run_until_complete(agen.__anext__())
                except StopAsyncIteration:
                    break
        finally:
            loop.close()

    return sync_generator(), meta


# ── Non-streaming (CLI / test_cli.py) ─────────────────────────
def run_agent(user_query: str, session_id: str = "default") -> dict:
    config = {"configurable": {"thread_id": session_id}}
    result = agent_graph.invoke(
        {"messages": [HumanMessage(content=user_query)]},
        config=config,
    )
    final_text = result["messages"][-1].content or ""
    tool_calls = [
        m.name for m in result["messages"]
        if hasattr(m, "name") and m.name in TOOL_NAMES
    ]
    output = check_output(final_text, tool_calls)
    return {"answer": output["text"], "tool_calls": tool_calls, "warnings": output["issues"]}
