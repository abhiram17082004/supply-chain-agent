import pandas as pd

df = pd.read_csv("data/raw/DataCoSupplyChainDataset.csv", encoding="ISO-8859-1")

print(f"Shape: {df.shape[0]:,} rows x {df.shape[1]} columns\n")

print("=== COLUMNS ===")
for col in df.columns:
    sample = df[col].dropna().iloc[0] if df[col].notna().any() else "N/A"
    print(f"  {col}: {df[col].dtype} | sample: {sample}")

print("\n=== DELIVERY STATUS ===")
print(df["Delivery Status"].value_counts())

print("\n=== MARKETS ===")
print(df["Market"].value_counts())

print("\n=== SHIPPING MODES ===")
print(df["Shipping Mode"].value_counts())

print("\n=== TOP CATEGORIES ===")
print(df["Category Name"].value_counts().head(10))

print("\n=== CUSTOMER SEGMENTS ===")
print(df["Customer Segment"].value_counts())
