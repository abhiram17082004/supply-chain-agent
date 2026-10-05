import sys, os
sys.path.insert(0, os.path.abspath("."))
import duckdb
import chromadb

DB_PATH     = "data/processed/supply_chain.duckdb"
VECTOR_PATH = "data/vector_store/"

conn = duckdb.connect(DB_PATH, read_only=True)

print("=" * 60)
print("PART 1 — DUCKDB (Structured Data)")
print("=" * 60)

total = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
cols  = len(conn.execute("DESCRIBE orders").fetchdf())
print(f"\nShape: {total:,} rows x {cols} columns")

print("\n--- Delivery Status ---")
for r in conn.execute("""
    SELECT delivery_status, COUNT(*) as n,
           ROUND(COUNT(*)*100.0/180519,1) as pct
    FROM orders GROUP BY delivery_status ORDER BY n DESC
""").fetchall():
    print(f"  {r[0]:<30} {r[1]:>8,}  ({r[2]}%)")

print("\n--- Markets ---")
for r in conn.execute("""
    SELECT market, COUNT(*) as n, ROUND(SUM(sales),0) as rev
    FROM orders GROUP BY market ORDER BY n DESC
""").fetchall():
    print(f"  {r[0]:<20} {r[1]:>8,} orders   ${r[2]:>12,.0f} revenue")

print("\n--- Shipping Modes ---")
for r in conn.execute("""
    SELECT shipping_mode, COUNT(*) as n,
           ROUND(AVG(CASE WHEN delivery_status='Late delivery'
                     THEN 1.0 ELSE 0.0 END)*100,1) as late_pct
    FROM orders GROUP BY shipping_mode ORDER BY n DESC
""").fetchall():
    print(f"  {r[0]:<20} {r[1]:>8,} orders   {r[2]}% late")

print("\n--- Top 10 Categories ---")
for r in conn.execute("""
    SELECT category_name, COUNT(*) as n
    FROM orders GROUP BY category_name ORDER BY n DESC LIMIT 10
""").fetchall():
    print(f"  {r[0]:<35} {r[1]:>7,} orders")

print("\n--- Customer Segments ---")
for r in conn.execute("""
    SELECT customer_segment, COUNT(*) as n,
           ROUND(AVG(order_profit_per_order),2) as avg_profit,
           ROUND(SUM(sales),0) as total_rev
    FROM orders GROUP BY customer_segment ORDER BY n DESC
""").fetchall():
    print(f"  {r[0]:<20} {r[1]:>8,} orders  avg profit ${r[2]}  revenue ${r[3]:,.0f}")

print("\n--- Revenue Summary ---")
r = conn.execute("""
    SELECT ROUND(SUM(sales),0) as total_rev,
           ROUND(AVG(sales),2) as avg_order,
           ROUND(SUM(order_profit_per_order),0) as total_profit,
           ROUND(AVG(order_profit_per_order),2) as avg_profit
    FROM orders
""").fetchone()
print(f"  Total Revenue:  ${r[0]:>15,.0f}")
print(f"  Avg Order:      ${r[1]:>15,.2f}")
print(f"  Total Profit:   ${r[2]:>15,.0f}")
print(f"  Avg Profit/Ord: ${r[3]:>15,.2f}")

conn.close()

print("\n")
print("=" * 60)
print("PART 2 — CHROMADB (RAG Vector Store)")
print("=" * 60)

chroma  = chromadb.PersistentClient(path=VECTOR_PATH)
col     = chroma.get_collection("supply_chain_knowledge")
count   = col.count()
results = col.get(include=["metadatas", "documents"])

print(f"\nTotal documents indexed: {count}")

sources = {}
for meta in results["metadatas"]:
    src = meta.get("source", "unknown")
    sources[src] = sources.get(src, 0) + 1

print("\n--- Document types in vector store ---")
for src, n in sorted(sources.items()):
    print(f"  {src:<25} {n} documents")

print("\n--- Sample documents (first of each type) ---")
seen = set()
for doc, meta in zip(results["documents"], results["metadatas"]):
    src = meta.get("source", "unknown")
    if src not in seen:
        seen.add(src)
        print(f"\n  [{src}]")
        print(f"  {doc[:200]}...")
