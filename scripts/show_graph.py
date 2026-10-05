import sys
import os
sys.path.insert(0, os.path.abspath("."))

from dotenv import load_dotenv
load_dotenv()

from src.agent.orchestrator import agent_graph

print("=== LangGraph Agent Structure ===\n")
print(agent_graph.get_graph().draw_mermaid())
