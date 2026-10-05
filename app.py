import sys, os
sys.path.insert(0, os.path.abspath("."))

import streamlit as st

try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, str):
            os.environ[_k] = _v
except Exception:
    pass

import uuid
import duckdb
from dotenv import load_dotenv
from src.guardrails.guards import check_input, check_output
from src.agent.orchestrator import stream_agent

load_dotenv()

DB_PATH = "data/processed/supply_chain.duckdb"

st.set_page_config(
    page_title="Supply Chain Agent",
    page_icon="✳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Session state ─────────────────────────────────────────────
if "messages"      not in st.session_state: st.session_state.messages    = []
if "session_id"    not in st.session_state: st.session_state.session_id  = str(uuid.uuid4())
if "dark_mode"     not in st.session_state: st.session_state.dark_mode   = True
if "sidebar_open"  not in st.session_state: st.session_state.sidebar_open = True
if "tool_counts" not in st.session_state:
    st.session_state.tool_counts = {
        "search_knowledge_base": 0,
        "run_sql_query": 0,
        "get_delivery_risk_report": 0
    }

DARK = st.session_state.dark_mode

# ── Theme colours ─────────────────────────────────────────────
if DARK:
    BG          = "#0d0d0d"
    BG_CARD     = "#1a1a1a"
    BG_INPUT    = "#1e1e1e"
    BG_SIDEBAR  = "#111111"
    BORDER      = "#2a2a2a"
    BORDER_HVR  = "#3a3a3a"
    ACCENT      = "#e8612c"
    TEXT_PRI    = "#ececec"
    TEXT_SEC    = "#8a8a8a"
    TEXT_MUT    = "#444444"
    USER_BG     = "#1e1e1e"
    AGENT_BG    = "#111111"
    PILL_BG     = "#1e1e1e"
    PILL_BDR    = "#2e2e2e"
    BADGE_BG    = "rgba(232,97,44,0.12)"
    BADGE_BDR   = "rgba(232,97,44,0.4)"
else:
    BG          = "#f9f9f9"
    BG_CARD     = "#ffffff"
    BG_INPUT    = "#ffffff"
    BG_SIDEBAR  = "#f3f3f3"
    BORDER      = "#e5e5e5"
    BORDER_HVR  = "#cccccc"
    ACCENT      = "#e8612c"
    TEXT_PRI    = "#1a1a1a"
    TEXT_SEC    = "#666666"
    TEXT_MUT    = "#aaaaaa"
    USER_BG     = "#f0f0f0"
    AGENT_BG    = "#ffffff"
    PILL_BG     = "#ffffff"
    PILL_BDR    = "#e0e0e0"
    BADGE_BG    = "rgba(232,97,44,0.08)"
    BADGE_BDR   = "rgba(232,97,44,0.3)"

# ── CSS ───────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewContainer"] > *,
[data-testid="stMain"] > *,
.stApp, .stApp > *,
section.main, section.main > * {{
    font-family: 'Inter', sans-serif !important;
    background-color: {BG} !important;
    color: {TEXT_PRI} !important;
}}
#MainMenu, footer, header, [data-testid="stHeader"] {{ display: none !important; }}
.stDeployButton {{ display: none !important; }}
[data-testid="stElementToolbar"] {{ display: none !important; }}
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}

/* ── Remove ALL empty spaces ── */
[data-testid="stSidebarHeader"] {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}}
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {{
    display: none !important;
}}
.stApp > header {{ display: none !important; }}
.stApp {{
    background: {BG} !important;
    min-height: 100vh;
}}
body, html {{
    background: {BG} !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow-x: hidden !important;
}}
[data-testid="stSidebar"] > div:first-child > div:first-child {{
    padding-top: 0 !important;
    margin-top: 0 !important;
}}
/* Kill any green/colored bottom bar */
[data-testid="stBottom"] + div,
.stApp::after,
.main::after {{
    display: none !important;
    height: 0 !important;
}}

/* ── Responsive ── */
@media (max-width: 1024px) {{
    .block-container {{
        padding: 0 1rem 2rem 1rem !important;
        max-width: 100% !important;
    }}
}}
@media (max-width: 768px) {{
    .block-container {{
        padding: 0 0.5rem 1rem 0.5rem !important;
        max-width: 100% !important;
    }}
    .greeting-title {{ font-size: 24px !important; }}
    .greeting-star  {{ font-size: 36px !important; }}
    .greeting-sub   {{ font-size: 13px !important; }}
    [data-testid="stChatMessage"] {{ max-width: 100% !important; }}
}}

.block-container {{
    padding: 0 2rem 10px 2rem !important;
    max-width: 900px !important;
    margin: 0 auto !important;
}}

/* ── Sidebar — kill ALL background overrides ── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > *,
[data-testid="stSidebar"] > * > *,
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"],
[data-testid="stSidebarNavItems"],
section[data-testid="stSidebar"],
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
    background: {BG_SIDEBAR} !important;
    background-color: {BG_SIDEBAR} !important;
}}
/* Kill the 96px bottom padding on stSidebarUserContent */
[data-testid="stSidebarUserContent"] {{
    padding-bottom: 0 !important;
    margin-bottom: 0 !important;
}}
[data-testid="stSidebar"] {{
    border-right: 1px solid {BORDER} !important;
}}
[data-testid="stSidebar"] > div:first-child {{
    padding: 1.2rem 1rem !important;
    background: {BG_SIDEBAR} !important;
}}

/* ── Sidebar logo ── */
.s-logo {{
    display: flex; align-items: center; gap: 10px;
    padding-bottom: 1rem;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 1rem;
}}
.s-logo-icon {{ font-size: 22px; }}
.s-logo-name {{ font-size: 14px; font-weight: 600; color: {TEXT_PRI}; }}
.s-logo-sub  {{ font-size: 11px; color: {TEXT_SEC}; }}

/* ── Section labels ── */
.s-label {{
    font-size: 10px; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: {TEXT_MUT};
    margin: 1rem 0 0.5rem 0;
}}

/* ── Stat rows ── */
.s-stat {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 5px 0; border-bottom: 1px solid {BORDER};
    font-size: 12px;
}}
.s-stat-label {{ color: {TEXT_SEC}; }}
.s-stat-value {{ font-weight: 600; color: {TEXT_PRI}; }}

/* ── Sidebar buttons ── */
.stButton > button {{
    width: 100%;
    background: transparent !important;
    color: {TEXT_SEC} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    padding: 6px 10px !important;
    text-align: left !important;
    transition: all 0.15s !important;
    font-family: 'Inter', sans-serif !important;
}}
.stButton > button:hover {{
    background: {BG_CARD} !important;
    border-color: {BORDER_HVR} !important;
    color: {TEXT_PRI} !important;
}}

/* ── Main page header ── */
.main-header {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 0 0 0;
}}
.main-header-left {{
    display: flex; align-items: center; gap: 8px;
}}
.main-header-title {{
    font-size: 14px; font-weight: 600; color: {TEXT_PRI};
}}

/* ── Empty state / greeting ── */
.greeting-wrap {{
    text-align: center;
    padding: 3rem 2rem 2rem 2rem;
}}
.greeting-star {{
    font-size: 48px;
    color: {ACCENT};
    line-height: 1;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: center;
}}
.greeting-title {{
    font-size: 32px; font-weight: 600;
    color: {TEXT_PRI}; margin-bottom: 0.5rem;
    letter-spacing: -0.02em;
}}
.greeting-sub {{
    font-size: 15px; color: {TEXT_SEC}; margin-bottom: 2.5rem;
}}

/* ── Suggestion pills ── */
.pills-row {{
    display: flex; flex-wrap: wrap;
    gap: 8px; justify-content: center;
    margin-top: 1rem;
}}
.pill {{
    background: {PILL_BG}; color: {TEXT_SEC};
    border: 1px solid {PILL_BDR}; border-radius: 20px;
    padding: 7px 16px; font-size: 13px; cursor: pointer;
    transition: all 0.15s; white-space: nowrap;
}}
.pill:hover {{
    border-color: {ACCENT}; color: {TEXT_PRI};
    background: {BG_CARD};
}}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {{
    background: transparent !important;
    border: none !important;
    max-width: 780px;
    margin: 0 auto;
}}
.stChatMessageContent {{
    background: transparent !important;
    border: none !important;
    font-size: 15px !important;
    line-height: 1.65 !important;
    color: {TEXT_PRI} !important;
}}

/* ── Tool badge ── */
.tool-badge {{
    display: inline-flex; align-items: center; gap: 4px;
    background: {BADGE_BG}; color: {ACCENT};
    border: 1px solid {BADGE_BDR}; border-radius: 20px;
    padding: 2px 10px 2px 7px; font-size: 11px;
    font-weight: 500; margin: 6px 3px 2px 0;
}}

/* ── Chat input — Claude style ── */
[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] {{
    background-color: {BG} !important;
    padding: 6px 0 6px 0 !important;
    margin: 0 !important;
}}
[data-testid="stBottomBlockContainer"] > div {{
    background-color: {BG} !important;
    padding: 0 4rem !important;
    max-width: 900px !important;
    margin: 0 auto !important;
}}
[data-testid="stChatInput"] {{
    border-radius: 16px !important;
}}
[data-testid="stChatInput"] > div {{
    background: {BG_INPUT} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.25) !important;
    position: relative !important;
    padding-bottom: 36px !important;
}}
[data-testid="stChatInput"] > div:focus-within {{
    border-color: {ACCENT}55 !important;
    box-shadow: 0 4px 24px rgba(232,97,44,0.1) !important;
}}
[data-testid="stChatInput"] > div > div {{
    background: transparent !important;
    border: none !important;
}}
[data-testid="stChatInput"] textarea {{
    color: {TEXT_PRI} !important;
    background: transparent !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    min-height: 52px !important;
    max-height: 200px !important;
    padding: 16px 16px 4px 18px !important;
    line-height: 1.6 !important;
}}
/* Bottom info bar inside the input box */
[data-testid="stChatInput"] > div::after {{
    content: "⚡ Groq  ·  openai/gpt-oss-120b  ·  Supply Chain Agent" !important;
    position: absolute !important;
    bottom: 10px !important;
    left: 18px !important;
    font-size: 11px !important;
    font-family: 'Inter', sans-serif !important;
    color: {TEXT_MUT} !important;
    pointer-events: none !important;
    white-space: nowrap !important;
    letter-spacing: 0.02em !important;
}}
/* Submit button */
[data-testid="stChatInput"] button {{
    background: {ACCENT} !important;
    border-radius: 10px !important;
    width: 32px !important;
    height: 32px !important;
    bottom: 8px !important;
    right: 10px !important;
    border: none !important;
}}
[data-testid="stChatInput"] button:hover {{
    opacity: 0.85 !important;
}}

/* ── Tables ── */
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:8px 0; }}
th {{
    background: {BG_CARD} !important; color: {ACCENT} !important;
    font-weight:600; padding:8px 12px;
    border-bottom: 2px solid {BORDER} !important;
    border: 1px solid {BORDER} !important;
}}
td {{ padding:7px 12px; border:1px solid {BORDER} !important; color:{TEXT_PRI}; }}
tr:nth-child(even) td {{ background: rgba(128,128,128,0.04); }}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 4px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 10px; }}

hr {{ border-color: {BORDER} !important; margin: 0.6rem 0 !important; }}
p, li, div {{ color: {TEXT_PRI}; }}

/* ── Header theme icon button ── */
.header-theme-btn > div > button {{
    width: 32px !important;
    min-width: 32px !important;
    height: 32px !important;
    min-height: 32px !important;
    border-radius: 8px !important;
    background: transparent !important;
    border: 1px solid {BORDER} !important;
    padding: 0 !important;
    font-size: 15px !important;
    line-height: 1 !important;
    transition: all 0.15s !important;
}}
.header-theme-btn > div > button:hover {{
    background: {BG_CARD} !important;
    border-color: {BORDER_HVR} !important;
}}
.header-theme-btn > div > button::after {{
    display: none !important;
}}
.header-theme-btn > div > button p {{
    font-size: 15px !important;
    margin: 0 !important;
    line-height: 1 !important;
    color: {TEXT_SEC} !important;
}}
/* Sidebar column gap for header row */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {{
    gap: 0 !important;
    align-items: center !important;
}}

/* Move theme button column down */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:nth-child(2) {{
    transform: translateY(10px) !important;
}}



/* ── Theme toggle pill (sidebar) ── */
.theme-btn > div > button {{
    width: 100% !important;
    height: 38px !important;
    border-radius: 19px !important;
    background: {'#2a2a2a' if DARK else ACCENT} !important;
    border: {'1px solid #444' if DARK else 'none'} !important;
    padding: 0 5px 0 12px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    position: relative !important;
    overflow: hidden !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
}}
.theme-btn > div > button:hover {{
    opacity: 0.85 !important;
}}
.theme-btn > div > button::after {{
    content: '' !important;
    width: 26px !important;
    height: 26px !important;
    border-radius: 50% !important;
    background: white !important;
    position: absolute !important;
    right: 6px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.25) !important;
    z-index: 2 !important;
}}
.theme-btn > div > button p,
.theme-btn > div > button [data-testid="stMarkdownContainer"] p {{
    font-size: 16px !important;
    margin: 0 !important;
    position: relative !important;
    z-index: 3 !important;
    line-height: 1 !important;
    color: white !important;
}}
</style>
""", unsafe_allow_html=True)


# ── Sidebar visibility via session state ─────────────────────
if not st.session_state.sidebar_open:
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    .block-container { max-width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)


# ── Cached stats ──────────────────────────────────────────────
@st.cache_data
def get_stats():
    c = duckdb.connect(DB_PATH, read_only=True)
    s = {
        "orders":  c.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "markets": c.execute("SELECT COUNT(DISTINCT market) FROM orders").fetchone()[0],
        "cats":    c.execute("SELECT COUNT(DISTINCT category_name) FROM orders").fetchone()[0],
        "late":    c.execute("SELECT ROUND(AVG(CASE WHEN delivery_status='Late delivery' THEN 1.0 ELSE 0.0 END)*100,1) FROM orders").fetchone()[0],
        "revenue": c.execute("SELECT ROUND(SUM(sales)/1000000,1) FROM orders").fetchone()[0],
    }
    c.close()
    return s

TOOL_META = {
    "search_knowledge_base":    {"icon": "🔍", "label": "Search"},
    "run_sql_query":            {"icon": "🗄️",  "label": "SQL"},
    "get_delivery_risk_report": {"icon": "⚠️",  "label": "Risk"},
}

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    _col_logo, _col_btn = st.columns([5, 1], gap="small")
    with _col_logo:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px;">
            <span class="s-logo-icon">🔗</span>
            <div>
                <div class="s-logo-name">Supply Chain Agent</div>
                <div class="s-logo-sub">DataCo Global · 180K orders</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with _col_btn:
        st.markdown('<div class="header-theme-btn">', unsafe_allow_html=True)
        _icon = "🌙" if DARK else "☀️"
        if st.button(_icon, key="theme_toggle"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="border-bottom:1px solid {BORDER}; margin-bottom:1rem;"></div>', unsafe_allow_html=True)

    # New chat button — top of sidebar
    st.markdown("""
    <style>
    .new-chat-btn > div > button {
        background: #1a1a1a !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 8px !important;
        color: #cccccc !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        padding: 6px 12px !important;
        width: auto !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        transition: all 0.15s !important;
        margin-bottom: 0.8rem !important;
    }
    .new-chat-btn > div > button:hover {
        background: #252525 !important;
        border-color: #3a3a3a !important;
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
    if st.button("New chat", key="clear"):
        st.session_state.messages   = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.tool_counts = {k: 0 for k in st.session_state.tool_counts}
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    try:
        s = get_stats()
        st.markdown('<div class="s-label">Dataset</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="s-stat"><span class="s-stat-label">📦 Orders</span>
             <span class="s-stat-value">{s['orders']//1000}K</span></div>
        <div class="s-stat"><span class="s-stat-label">🌍 Markets</span>
             <span class="s-stat-value">{s['markets']}</span></div>
        <div class="s-stat"><span class="s-stat-label">🏷️ Categories</span>
             <span class="s-stat-value">{s['cats']}</span></div>
        <div class="s-stat"><span class="s-stat-label">⏱️ Late Rate</span>
             <span class="s-stat-value" style="color:#e8612c">{s['late']}%</span></div>
        <div class="s-stat" style="border:none"><span class="s-stat-label">💰 Revenue</span>
             <span class="s-stat-value" style="color:#4caf7d">${s['revenue']}M</span></div>
        """, unsafe_allow_html=True)
    except Exception:
        pass

    tc = st.session_state.tool_counts
    st.markdown('<div class="s-label">Tools this session</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="s-stat"><span class="s-stat-label">🔍 Knowledge</span>
         <span class="s-stat-value">{tc['search_knowledge_base']}x</span></div>
    <div class="s-stat"><span class="s-stat-label">🗄️ SQL</span>
         <span class="s-stat-value">{tc['run_sql_query']}x</span></div>
    <div class="s-stat" style="border:none"><span class="s-stat-label">⚠️ Risk</span>
         <span class="s-stat-value">{tc['get_delivery_risk_report']}x</span></div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="s-label">Suggestions</div>', unsafe_allow_html=True)
    examples = [
        "Which market has worst delivery rate?",
        "Compare all shipping modes",
        "Top 5 late delivery categories",
        "Revenue by customer segment",
        "How many orders were canceled?",
        "Summarize LATAM performance",
        "Best performing department?",
        "Same Day vs Standard Class?",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state["prefill"] = ex
            st.rerun()





# ── Empty state — greeting + pills ───────────────────────────
QUICK_PILLS = [
    ("📦", "Late deliveries by market"),
    ("💰", "Revenue breakdown"),
    ("🚚", "Shipping mode comparison"),
    ("⚠️", "Highest risk categories"),
    ("🌍", "LATAM performance"),
    ("📊", "Profit by segment"),
]

if not st.session_state.messages:
    st.markdown(f"""
    <div class="greeting-wrap">
        <div class="greeting-star">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="32" cy="32" r="32" fill="{ACCENT}" fill-opacity="0.12"/>
                <!-- Node 1 -->
                <circle cx="12" cy="32" r="6" fill="{ACCENT}"/>
                <!-- Node 2 (center, larger) -->
                <circle cx="32" cy="32" r="8" fill="{ACCENT}"/>
                <!-- Node 3 -->
                <circle cx="52" cy="32" r="6" fill="{ACCENT}"/>
                <!-- Connector lines -->
                <line x1="18" y1="32" x2="24" y2="32" stroke="{ACCENT}" stroke-width="2.5" stroke-linecap="round"/>
                <line x1="40" y1="32" x2="46" y2="32" stroke="{ACCENT}" stroke-width="2.5" stroke-linecap="round"/>
                <!-- Top node -->
                <circle cx="32" cy="14" r="5" fill="{ACCENT}" fill-opacity="0.6"/>
                <line x1="32" y1="19" x2="32" y2="24" stroke="{ACCENT}" stroke-width="2.5" stroke-linecap="round" stroke-opacity="0.6"/>
                <!-- Bottom node -->
                <circle cx="32" cy="50" r="5" fill="{ACCENT}" fill-opacity="0.6"/>
                <line x1="32" y1="40" x2="32" y2="45" stroke="{ACCENT}" stroke-width="2.5" stroke-linecap="round" stroke-opacity="0.6"/>
            </svg>
        </div>
        <div class="greeting-title">Hello, supply chain analyst</div>
        <div class="greeting-sub">
            Ask me anything about 180K orders across 5 global markets
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Pill buttons as columns
    pill_cols = st.columns(3)
    for i, (icon, label) in enumerate(QUICK_PILLS):
        with pill_cols[i % 3]:
            if st.button(f"{icon}  {label}", key=f"pill_{i}", use_container_width=True):
                st.session_state["prefill"] = label
                st.rerun()


# ── Render messages ───────────────────────────────────────────
for msg in st.session_state.messages:
    avatar = "🧑" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg.get("tools"):
            badges = "".join(
                f'<span class="tool-badge">'
                f'{TOOL_META.get(t,{"icon":"🔧"})["icon"]} '
                f'{TOOL_META.get(t,{"label":t})["label"]}</span>'
                for t in msg["tools"]
            )
            st.markdown(badges, unsafe_allow_html=True)


# ── Input ─────────────────────────────────────────────────────
query      = st.session_state.pop("prefill", None)
user_input = st.chat_input("Ask about deliveries, markets, products, performance...")
if user_input:
    query = user_input

if query:
    clean = query.lstrip("📦💰🚚⚠️🌍📊 ").strip()

    with st.chat_message("user", avatar="🧑"):
        st.markdown(clean)
    st.session_state.messages.append({"role": "user", "content": clean})

    guard = check_input(clean)
    if not guard.is_safe:
        with st.chat_message("assistant", avatar="🤖"):
            st.warning(guard.reason)
        st.session_state.messages.append({
            "role": "assistant", "content": guard.reason,
            "tools": [], "warnings": []
        })
    else:
        with st.chat_message("assistant", avatar="🤖"):
            gen, meta = stream_agent(guard.sanitized, st.session_state.session_id)
            full_text = st.write_stream(gen)

            if meta["tool_calls"]:
                badges = "".join(
                    f'<span class="tool-badge">'
                    f'{TOOL_META.get(t,{"icon":"🔧"})["icon"]} '
                    f'{TOOL_META.get(t,{"label":t})["label"]}</span>'
                    for t in meta["tool_calls"]
                )
                st.markdown(badges, unsafe_allow_html=True)

        output = check_output(full_text, meta["tool_calls"])
        st.session_state.messages.append({
            "role": "assistant", "content": full_text,
            "tools": meta["tool_calls"], "warnings": output["issues"]
        })
        for t in meta["tool_calls"]:
            if t in st.session_state.tool_counts:
                st.session_state.tool_counts[t] += 1

        st.rerun()
