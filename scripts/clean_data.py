import sys
import os
sys.path.insert(0, os.path.abspath("."))

import duckdb

DB_PATH = "data/processed/supply_chain.duckdb"

# ── Columns to drop ───────────────────────────────────────────
DROP_PII = [
    "customer_email",       # real email addresses
    "customer_fname",       # first name
    "customer_lname",       # last name
    "customer_password",    # passwords — serious security risk
    "customer_street",      # home address
]

DROP_USELESS = [
    "product_description",  # 100% null — zero non-null values
    "product_image",        # image URLs — no analytical value
    "order_zipcode",        # 86% null — too sparse to use
]


def clean():
    conn = duckdb.connect(DB_PATH)

    print("=== Before Cleaning ===")
    before = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    before_cols = len(conn.execute("DESCRIBE orders").fetchdf())
    print(f"  Rows: {before:,}   Columns: {before_cols}")

    # ── Step 1: Drop PII columns ──────────────────────────────
    print("\n--- Dropping PII columns ---")
    for col in DROP_PII:
        try:
            conn.execute(f"ALTER TABLE orders DROP COLUMN {col}")
            print(f"  Dropped: {col}")
        except Exception as e:
            print(f"  Skip {col}: {e}")

    # ── Step 2: Drop useless columns ─────────────────────────
    print("\n--- Dropping useless columns ---")
    for col in DROP_USELESS:
        try:
            conn.execute(f"ALTER TABLE orders DROP COLUMN {col}")
            print(f"  Dropped: {col}")
        except Exception as e:
            print(f"  Skip {col}: {e}")

    # ── Step 3: Fix minor nulls ───────────────────────────────
    print("\n--- Fixing nulls ---")
    conn.execute("UPDATE orders SET customer_zipcode = 0 WHERE customer_zipcode IS NULL")
    print("  customer_zipcode nulls → 0")

    # ── Step 4: Verify result ─────────────────────────────────
    print("\n=== After Cleaning ===")
    after = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    after_cols = len(conn.execute("DESCRIBE orders").fetchdf())
    print(f"  Rows: {after:,}   Columns: {after_cols}")
    print(f"  Columns removed: {before_cols - after_cols}")
    print(f"  Rows unchanged: {before == after}")

    print("\n--- Remaining columns ---")
    schema = conn.execute("DESCRIBE orders").fetchdf()
    for _, row in schema.iterrows():
        print(f"  {row['column_name']:45} {row['column_type']}")

    print("\n--- Null check on remaining columns ---")
    for col in schema["column_name"]:
        nulls = conn.execute(f"SELECT COUNT(*) FROM orders WHERE {col} IS NULL").fetchone()[0]
        if nulls > 0:
            print(f"  WARNING: {col} still has {nulls:,} nulls")
    print("  Null check complete.")

    conn.close()
    print(f"\nCleaned database saved: {DB_PATH}")


if __name__ == "__main__":
    clean()
