import duckdb

conn = duckdb.connect("data/processed/supply_chain.duckdb", read_only=True)

print("=== NULL COUNTS ===")
schema = conn.execute("DESCRIBE orders").fetchdf()
for col in schema["column_name"]:
    nulls = conn.execute(f"SELECT COUNT(*) FROM orders WHERE {col} IS NULL").fetchone()[0]
    if nulls > 0:
        print(f"  {col}: {nulls:,} nulls")

print()
print("=== DUPLICATES ===")
total = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
distinct = conn.execute("SELECT COUNT(*) FROM (SELECT DISTINCT * FROM orders)").fetchone()[0]
print(f"  Total rows:    {total:,}")
print(f"  Distinct rows: {distinct:,}")
print(f"  Duplicates:    {total - distinct:,}")

print()
print("=== PII COLUMNS IN DATASET ===")
pii_cols = ["customer_email", "customer_fname", "customer_lname", "customer_password", "customer_street"]
for col in pii_cols:
    sample = conn.execute(f"SELECT {col} FROM orders WHERE {col} IS NOT NULL LIMIT 1").fetchone()
    val = sample[0] if sample else "empty"
    print(f"  {col}: {val}")

print()
print("=== USELESS COLUMNS ===")
useless = ["product_description", "product_image", "product_status"]
for col in useless:
    non_null = conn.execute(f"SELECT COUNT(*) FROM orders WHERE {col} IS NOT NULL").fetchone()[0]
    print(f"  {col}: {non_null:,} non-null values")

print()
print("=== DELIVERY STATUS VALUES ===")
rows = conn.execute("SELECT delivery_status, COUNT(*) as cnt FROM orders GROUP BY delivery_status").fetchall()
for r in rows:
    print(f"  {r[0]}: {r[1]:,}")

print()
print("=== ORDER STATUS VALUES ===")
rows = conn.execute("SELECT order_status, COUNT(*) as cnt FROM orders GROUP BY order_status ORDER BY cnt DESC").fetchall()
for r in rows:
    print(f"  {r[0]}: {r[1]:,}")

conn.close()
