# Supply Chain Intelligence Agent

A production-grade conversational AI agent that answers natural language questions about supply chain data. Built with **LangGraph**, **Groq**, **RAG**, and **Streamlit** — at **zero cost**.

---

## What It Does

Type any supply chain question in plain English and get instant, data-backed answers:

- *"Which market has the worst late delivery rate?"*
- *"Compare all shipping modes by performance"*
- *"What is LATAM and how is it performing?"*
- *"Top 5 product categories with highest delays"*
- *"Total revenue by customer segment"*

The agent queries **180,519 real supply chain orders** across 5 global markets and streams answers word by word — no waiting, no guessing.

---

## Architecture

```
User Question
      │
      ▼
Input Guardrail (LangChain RunnableLambda)
      │
      ▼
LangGraph Agent (StateGraph + MemorySaver)
      │
      ├── search_knowledge_base  → ChromaDB (RAG / semantic search)
      ├── run_sql_query          → DuckDB (exact SQL queries)
      └── get_delivery_risk_report → DuckDB (ranked analytics)
      │
      ▼
Output Parser (LangChain StrOutputParser)
      │
      ▼
Streamlit UI (streamed token by token)
```

---

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| LLM | Groq (openai/gpt-oss-120b) | Language model — free tier |
| Agent Framework | LangGraph | Agent loop, memory, streaming |
| Tool Layer | LangChain | Tool definitions, chains |
| Vector Store | ChromaDB + HuggingFace Embeddings | RAG semantic search |
| SQL Database | DuckDB | Structured analytical queries |
| Rate Limiting | slowapi | 10 req/min per IP |
| REST API | FastAPI | External integrations |
| Frontend | Streamlit | Chat UI |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Local, free, 384-dim |

**Total infrastructure cost: $0**

---

## Project Structure

```
SupplyChainAgent/
│
├── app.py                        # Streamlit frontend
├── requirements.txt
├── .env                          # API keys (never committed)
├── .streamlit/config.toml
│
├── src/
│   ├── agent/
│   │   └── orchestrator.py       # LangGraph agent + streaming
│   ├── tools/
│   │   ├── lc_tools.py           # 3 LangChain tools
│   │   └── risk_tool.py          # DuckDB risk analytics
│   ├── guardrails/
│   │   └── guards.py             # Input/output safety (LangChain)
│   ├── security/
│   │   └── limiter.py            # Rate limiter (slowapi)
│   ├── ingestion/
│   │   ├── db_loader.py          # CSV → DuckDB (run once)
│   │   └── rag_builder.py        # DuckDB → ChromaDB (run once)
│   └── api/
│       ├── main.py               # FastAPI app
│       └── routes/chat.py        # /chat endpoint
│
├── scripts/
│   ├── download_data.py          # Kaggle dataset download
│   ├── ingest_all.py             # Run db_loader + rag_builder
│   ├── clean_data.py             # Remove PII + useless columns
│   └── test_cli.py               # Test agent without UI
│
└── data/
    ├── processed/
    │   └── supply_chain.duckdb   # 180,519 rows, 45 columns (19MB)
    └── vector_store/             # ChromaDB index (37 documents, 0.5MB)
```

---

## The Dataset

**DataCo Smart Supply Chain** — sourced from Kaggle.

| Metric | Value |
|---|---|
| Total orders | 180,519 |
| Columns | 45 (after cleaning) |
| Markets | LATAM, Europe, Pacific Asia, USCA, Africa |
| Shipping modes | First Class, Second Class, Standard Class, Same Day |
| Customer segments | Consumer, Corporate, Home Office |
| Late delivery rate | 54.8% |
| Total revenue | $36.8M |

After cleaning: PII removed (emails, passwords, names, addresses), 100% null columns dropped, zero duplicates.

---

## The 3 Agent Tools

### 1. `search_knowledge_base` — RAG / Semantic Search
Searches 37 pre-built knowledge documents using vector similarity.

- **Used for:** Open-ended questions, summaries, definitions ("What is LATAM?")
- **How:** Query → 384-dim embedding → ChromaDB cosine similarity → top 4 documents → LLM answer
- **Documents:** 5 market reports, 25 category profiles, 4 shipping analyses, 3 segment profiles

### 2. `run_sql_query` — Exact SQL Queries
Runs validated SQL SELECT queries against 180,519 orders in DuckDB.

- **Used for:** Exact counts, totals, averages, filters, rankings
- **Security:** SELECT only — DROP, DELETE, INSERT, UPDATE are blocked
- **Example:** `SELECT COUNT(*) FROM orders WHERE market='Europe' AND delivery_status='Shipping canceled'`

### 3. `get_delivery_risk_report` — Ranked Analytics
Pre-built GROUP BY analysis ranked by late delivery rate.

- **Used for:** "Which X has worst/best Y?" questions
- **Dimensions:** category_name, market, shipping_mode, department_name, order_region, customer_segment
- **Returns:** late_rate_pct, avg_delay_days, avg_profit_usd, total_revenue_usd

---

## Setup

### Prerequisites
- Python 3.11+
- Groq API key (free at [console.groq.com](https://console.groq.com))
- Kaggle account + API key (free at [kaggle.com](https://kaggle.com))

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/supply-chain-agent.git
cd supply-chain-agent
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure environment

Create `.env`:
```env
GROQ_API_KEY=gsk_your_groq_key_here
AGENT_API_KEY=your_secret_api_key
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key
```

### 3. Download and process data

> **Note:** If Kaggle download fails (corporate proxy), manually download `DataCoSupplyChainDataset.csv` from Kaggle and place it in `data/raw/`.

```bash
python scripts/download_data.py   # download Kaggle dataset
python scripts/ingest_all.py      # load into DuckDB + build RAG
python scripts/clean_data.py      # remove PII + useless columns
```

> The processed data files (`supply_chain.duckdb` + `vector_store/`) are already included in this repository. You can skip this step if cloning from GitHub.

### 4. Run the app

```bash
streamlit run app.py --server.fileWatcherType none
```

Open `http://localhost:8501` in your browser.

---

## REST API

The FastAPI server runs separately and exposes the agent as a REST endpoint.

### Start the API server

```bash
uvicorn src.api.main:app --reload --port 8000
```

### Chat endpoint

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: your_secret_api_key" \
  -d '{"query": "Which market has the worst delivery rate?", "session_id": "user_123"}'
```

**Response:**
```json
{
  "answer": "Based on the delivery risk report...",
  "tools_used": ["get_delivery_risk_report"],
  "warnings": [],
  "session_id": "user_123"
}
```

### Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat` | Send a question, get an answer |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive API documentation (Swagger) |

**Rate limit:** 10 requests per minute per IP.
**Auth:** `x-api-key` header required.

---

## Deployment — Streamlit Cloud (Free)

1. Push this repo to GitHub (public)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set main file to `app.py`
5. Add secrets in **Advanced Settings**:

```toml
GROQ_API_KEY = "gsk_your_groq_key"
AGENT_API_KEY = "your_secret_key"
```

6. Click **Deploy**

Your app will be live at `https://yourname-supply-chain-agent-app.streamlit.app`

---

## How the Agent Works

```
1. You type a question
2. Input guardrail validates it (length, safety)
3. LangGraph loads your conversation history (MemorySaver)
4. LLM reads: system prompt + history + your question + tool schemas
5. LLM decides which tool to call and with what arguments
6. ToolNode executes the tool (queries DuckDB or ChromaDB)
7. LLM reads the tool result and writes the answer
8. astream_events fires token by token → appears word by word in UI
9. Tool badges show which tools were called
10. MemorySaver saves the full conversation for next message
```

---

## Data Flow

```
Kaggle CSV (raw)
      ↓ db_loader.py
DuckDB (180K rows, SQL queries)
      ↓ rag_builder.py
ChromaDB (37 docs, vector search)
      ↓
Agent tools query both stores
      ↓
LLM synthesizes answer
      ↓
Streamlit streams to user
```

---

## Guardrails & Security

| Layer | What it checks | Framework |
|---|---|---|
| Input length | Blocks queries over 1500 characters | LangChain RunnableLambda |
| Empty input | Blocks empty messages | LangChain RunnableLambda |
| SQL injection | Blocks non-SELECT SQL statements | Custom validation |
| Dangerous keywords | Blocks DROP, DELETE, INSERT etc. | Custom validation |
| Rate limiting | 10 requests/minute per IP | slowapi |
| API auth | x-api-key header required | FastAPI Header dependency |
| Output parsing | Cleans LLM text | LangChain StrOutputParser |
| Topic adherence | System prompt instructs LLM to decline off-topic questions | Prompt engineering |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq API key (get free at console.groq.com) |
| `AGENT_API_KEY` | ✅ | Your custom secret key for the REST API |
| `KAGGLE_USERNAME` | Only for download | Your Kaggle username |
| `KAGGLE_KEY` | Only for download | Your Kaggle API key |

---

## License

MIT License — free to use, modify, and distribute.

---

## Acknowledgements

- Dataset: [DataCo Smart Supply Chain](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data) by shashwatwork on Kaggle
- LLM: [Groq](https://groq.com) free tier
- Agent framework: [LangGraph](https://langchain-ai.github.io/langgraph/) by LangChain
- Embeddings: [sentence-transformers](https://www.sbert.net/) — all-MiniLM-L6-v2
