import re
import json
import duckdb
from typing import Optional

from langchain_core.tools import tool, StructuredTool
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel, Field

VECTOR_PATH = "data/vector_store/"
DB_PATH     = "data/processed/supply_chain.duckdb"

BLOCKED = ["drop","delete","insert","update","create",
           "alter","truncate","exec","execute","--",";"]

# ── LangChain Vector Store + Embeddings ───────────────────────
_embeddings  = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
_vectorstore = Chroma(
    persist_directory=VECTOR_PATH,
    collection_name="supply_chain_knowledge",
    embedding_function=_embeddings,
)


# ── Tool 1: RAG Search (LangChain @tool) ─────────────────────
@tool
def search_knowledge_base(query: str, n_results: int = 4) -> str:
    """Search the supply chain knowledge base semantically.
    Use for: market summaries, category profiles, shipping comparisons,
    customer segment overviews, and open-ended conceptual questions."""
    docs = _vectorstore.similarity_search(query, k=n_results)
    return "\n\n".join(doc.page_content for doc in docs)


# ── Tool 2: SQL Query (LangChain StructuredTool + raw DuckDB) ─
class SQLInput(BaseModel):
    query: str = Field(description=(
        "SQL SELECT against table 'orders'. "
        "Columns: delivery_status, days_for_shipping_real, "
        "days_for_shipment_scheduled, late_delivery_risk, category_name, "
        "market (LATAM/Europe/Pacific Asia/USCA/Africa), order_region, "
        "shipping_mode, customer_segment, department_name, order_status, "
        "sales, order_profit_per_order, order_item_profit_ratio, "
        "order_item_discount_rate, order_item_quantity, product_name, "
        "product_price. Only SELECT allowed."
    ))


def _run_sql(query: str) -> str:
    if not re.match(r"^\s*SELECT\b", query, re.IGNORECASE):
        return "Error: Only SELECT statements are permitted"
    for kw in BLOCKED:
        if kw in query.lower():
            return f"Error: Blocked keyword '{kw}'"
    conn = duckdb.connect(DB_PATH, read_only=True)
    try:
        df = conn.execute(query).fetchdf()
        return df.head(50).to_string(index=False)
    except Exception as e:
        return f"Error: {e}"
    finally:
        conn.close()


run_sql_query = StructuredTool.from_function(
    func=_run_sql,
    name="run_sql_query",
    description=(
        "Run a SQL SELECT query against the supply chain orders table. "
        "Use for exact counts, aggregations, filters, rankings, calculations. "
        "Only SELECT allowed. Table: orders."
    ),
    args_schema=SQLInput,
)


# ── Tool 3: Delivery Risk Report (LangChain StructuredTool) ───
from src.tools.risk_tool import get_delivery_risk_report as _risk


class RiskInput(BaseModel):
    group_by: str = Field(description=(
        "Dimension to group by: category_name | market | shipping_mode | "
        "department_name | order_region | customer_segment"
    ))
    market: Optional[str] = Field(default=None, description=(
        "Optional filter: LATAM | Europe | Pacific Asia | USCA | Africa"
    ))
    limit: Optional[int] = Field(default=10, description="Top N results")


get_delivery_risk_report = StructuredTool.from_function(
    func=lambda group_by, market=None, limit=10: json.dumps(
        _risk(group_by, market, limit), default=str
    ),
    name="get_delivery_risk_report",
    description=(
        "Ranked delivery risk report grouped by a supply chain dimension. "
        "Best for: which category/market/shipping mode has worst/best performance."
    ),
    args_schema=RiskInput,
)


# ── Export ────────────────────────────────────────────────────
LANGCHAIN_TOOLS = [search_knowledge_base, run_sql_query, get_delivery_risk_report]
