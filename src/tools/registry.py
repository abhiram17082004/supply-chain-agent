from src.tools.rag_tool import search_knowledge_base
from src.tools.sql_tool import run_sql_query
from src.tools.risk_tool import get_delivery_risk_report

TOOL_FUNCTIONS = {
    "search_knowledge_base": search_knowledge_base,
    "run_sql_query": run_sql_query,
    "get_delivery_risk_report": get_delivery_risk_report,
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Semantic search over supply chain knowledge base. "
                "Use for: market summaries, category profiles, shipping comparisons, "
                "segment overviews, and open-ended or conceptual questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results (default 4, max 10)"
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_sql_query",
            "description": (
                "Run a SQL SELECT query against the supply chain orders table. "
                "Use for exact counts, aggregations, filters, rankings, and precise calculations. "
                "Table: orders. Only SELECT is allowed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A valid SQL SELECT statement against table 'orders'"
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_delivery_risk_report",
            "description": (
                "Get a ranked delivery risk breakdown grouped by a dimension. "
                "Best for: which category/market/shipping mode has worst or best delivery performance. "
                "group_by options: category_name, market, shipping_mode, "
                "department_name, order_region, customer_segment"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {
                        "type": "string",
                        "enum": [
                            "category_name", "market", "shipping_mode",
                            "department_name", "order_region", "customer_segment"
                        ]
                    },
                    "market": {
                        "type": "string",
                        "description": "Optional market filter: LATAM, Europe, Pacific Asia, USCA, Africa"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Top N results (default 10)"
                    }
                },
                "required": ["group_by"],
                "additionalProperties": False
            }
        }
    }
]
