import sys
import os
sys.path.insert(0, os.path.abspath("."))

from dotenv import load_dotenv
load_dotenv()

from src.agent.orchestrator import run_agent

QUESTIONS = [
    "Which product categories have the highest late delivery rate?",
    "What is the total revenue for each market?",
    "Compare delivery performance across all shipping modes",
    "Which customer segment is most profitable?",
    "How many orders were canceled across all markets?",
]

history = []

for i, q in enumerate(QUESTIONS, 1):
    print(f"\n{'='*65}")
    print(f"Q{i}: {q}")
    print("-" * 65)
    result = run_agent(q, history)
    print(f"Answer:\n{result['answer']}")
    print(f"\nTools used: {result['tool_calls']}")
    if result.get("warnings"):
        print(f"Warnings: {result['warnings']}")

    history.append({"role": "user", "content": q})
    history.append({"role": "assistant", "content": result["answer"]})
