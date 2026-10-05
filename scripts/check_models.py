import os
import sys
import httpx
sys.path.insert(0, os.path.abspath("."))

from dotenv import load_dotenv
load_dotenv()

from groq import Groq

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    http_client=httpx.Client(verify=False)
)

models = client.models.list()

print("Available models on your Groq account:\n")
for m in sorted(models.data, key=lambda x: x.id):
    print(f"  {m.id}")
