import duckdb
import chromadb
from sentence_transformers import SentenceTransformer

DB_PATH = "data/processed/supply_chain.duckdb"
VECTOR_PATH = "data/vector_store/"


def generate_documents(conn) -> list[dict]:
    docs = []

    # Market performance reports
    markets = conn.execute(
        "SELECT DISTINCT market FROM orders WHERE market IS NOT NULL"
    ).fetchdf()

    for _, row in markets.iterrows():
        m = row["market"].replace("'", "''")
        s = conn.execute(f"""
            SELECT
                COUNT(*) as total_orders,
                ROUND(AVG(CASE WHEN delivery_status='Late delivery' THEN 1.0 ELSE 0.0 END)*100,1) as late_pct,
                ROUND(AVG(order_profit_per_order),2) as avg_profit,
                ROUND(SUM(sales),0) as total_sales,
                COUNT(DISTINCT category_name) as num_categories,
                COUNT(DISTINCT shipping_mode) as num_ship_modes
            FROM orders WHERE market='{m}'
        """).fetchone()

        text = (
            f"Supply Chain Market Report: {row['market']}. "
            f"Total orders: {int(s[0]):,}. Late delivery rate: {s[1]}%. "
            f"Average profit per order: ${s[2]}. Total sales revenue: ${int(s[3]):,}. "
            f"Serves {s[4]} product categories via {s[5]} shipping modes. "
            f"This market is tracked for on-time delivery, revenue performance, and supplier reliability."
        )
        docs.append({
            "id": f"market_{row['market'].replace(' ', '_')}",
            "text": text,
            "source": "market_report",
            "market": row["market"]
        })

    # Category profiles
    cats = conn.execute("""
        SELECT category_name,
               COUNT(*) as orders,
               ROUND(AVG(CASE WHEN delivery_status='Late delivery' THEN 1.0 ELSE 0.0 END)*100,1) as late_pct,
               ROUND(AVG(order_item_profit_ratio)*100,1) as margin_pct,
               ROUND(SUM(sales),0) as revenue,
               ROUND(AVG(order_profit_per_order),2) as avg_profit
        FROM orders
        WHERE category_name IS NOT NULL
        GROUP BY category_name
        ORDER BY orders DESC
        LIMIT 25
    """).fetchdf()

    for _, row in cats.iterrows():
        text = (
            f"Product Category Profile: {row['category_name']}. "
            f"Total orders: {int(row['orders']):,}. "
            f"Late delivery rate: {row['late_pct']}%. "
            f"Average profit margin: {row['margin_pct']}%. "
            f"Total revenue: ${int(row['revenue']):,}. "
            f"Average profit per order: ${row['avg_profit']}."
        )
        docs.append({
            "id": f"cat_{row['category_name'].replace(' ', '_').replace('/', '_')}",
            "text": text,
            "source": "category_profile"
        })

    # Shipping mode analysis
    modes = conn.execute("""
        SELECT shipping_mode,
               COUNT(*) as orders,
               ROUND(AVG(days_for_shipping_real),1) as avg_actual,
               ROUND(AVG(days_for_shipment_scheduled),1) as avg_scheduled,
               ROUND(AVG(CASE WHEN delivery_status='Late delivery' THEN 1.0 ELSE 0.0 END)*100,1) as late_pct,
               ROUND(AVG(order_profit_per_order),2) as avg_profit
        FROM orders
        WHERE shipping_mode IS NOT NULL
        GROUP BY shipping_mode
    """).fetchdf()

    for _, row in modes.iterrows():
        delay = round(row["avg_actual"] - row["avg_scheduled"], 1)
        text = (
            f"Shipping Mode Analysis: {row['shipping_mode']}. "
            f"Used in {int(row['orders']):,} orders. "
            f"Average actual delivery: {row['avg_actual']} days. "
            f"Scheduled: {row['avg_scheduled']} days. "
            f"Average delay: {delay} days. "
            f"Late delivery rate: {row['late_pct']}%. "
            f"Average profit: ${row['avg_profit']} per order."
        )
        docs.append({
            "id": f"ship_{row['shipping_mode'].replace(' ', '_')}",
            "text": text,
            "source": "shipping_analysis"
        })

    # Customer segment profiles
    segs = conn.execute("""
        SELECT customer_segment,
               COUNT(*) as orders,
               ROUND(AVG(order_profit_per_order),2) as avg_profit,
               ROUND(SUM(sales),0) as total_sales,
               ROUND(AVG(CASE WHEN delivery_status='Late delivery' THEN 1.0 ELSE 0.0 END)*100,1) as late_pct
        FROM orders
        WHERE customer_segment IS NOT NULL
        GROUP BY customer_segment
    """).fetchdf()

    for _, row in segs.iterrows():
        text = (
            f"Customer Segment Profile: {row['customer_segment']}. "
            f"Total orders: {int(row['orders']):,}. "
            f"Average profit per order: ${row['avg_profit']}. "
            f"Total revenue: ${int(row['total_sales']):,}. "
            f"Late delivery rate: {row['late_pct']}%."
        )
        docs.append({
            "id": f"seg_{row['customer_segment'].replace(' ', '_')}",
            "text": text,
            "source": "segment_profile"
        })

    return docs


def build_vector_store():
    conn = duckdb.connect(DB_PATH, read_only=True)
    print("Generating knowledge documents from database...")
    docs = generate_documents(conn)
    conn.close()
    print(f"  Generated {len(docs)} documents")

    print("Loading embedding model (downloads ~90MB on first run)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("Embedding and indexing...")
    chroma = chromadb.PersistentClient(path=VECTOR_PATH)

    try:
        chroma.delete_collection("supply_chain_knowledge")
    except Exception:
        pass

    collection = chroma.create_collection("supply_chain_knowledge")

    texts = [d["text"] for d in docs]
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)

    collection.add(
        ids=[d["id"] for d in docs],
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=[{k: v for k, v in d.items() if k != "text"} for d in docs]
    )

    print(f"\nVector store ready: {collection.count()} documents indexed")
    print(f"Saved: {VECTOR_PATH}")


if __name__ == "__main__":
    build_vector_store()
