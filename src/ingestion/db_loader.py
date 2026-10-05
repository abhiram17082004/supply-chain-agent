import pandas as pd
import duckdb
import os

DB_PATH = "data/processed/supply_chain.duckdb"


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace(r"[^\w]", "", regex=True)
    )
    return df


def load_to_duckdb():
    csv_path = "data/raw/DataCoSupplyChainDataset.csv"

    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} not found. Run scripts/download_data.py first.")
        return

    print("Reading CSV...")
    df = pd.read_csv(csv_path, encoding="ISO-8859-1")
    df = clean_column_names(df)

    print(f"  Rows: {len(df):,}  Columns: {len(df.columns)}")

    conn = duckdb.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS orders")
    conn.execute("CREATE TABLE orders AS SELECT * FROM df")

    count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    print(f"\nDuckDB table 'orders' created: {count:,} rows")

    print("\nSchema:")
    schema = conn.execute("DESCRIBE orders").fetchdf()
    for _, row in schema.iterrows():
        print(f"  {row['column_name']:45} {row['column_type']}")

    conn.close()
    print(f"\nSaved: {DB_PATH}")


if __name__ == "__main__":
    load_to_duckdb()
