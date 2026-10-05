import os
import sys
sys.path.insert(0, os.path.abspath("."))

CSV_PATH = "data/raw/DataCoSupplyChainDataset.csv"

# If file already manually downloaded, skip the Kaggle API entirely
if os.path.exists(CSV_PATH):
    size_kb = os.path.getsize(CSV_PATH) // 1024
    print(f"Dataset already present: {CSV_PATH} ({size_kb} KB)")
    print("Skipping download.")
    sys.exit(0)

# Try Kaggle API download — may fail on corporate networks due to SSL proxy
from dotenv import load_dotenv
load_dotenv()

os.environ["KAGGLE_USERNAME"] = os.getenv("KAGGLE_USERNAME", "")
os.environ["KAGGLE_KEY"] = os.getenv("KAGGLE_KEY", "")

# Disable SSL verification for corporate proxy environments
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
os.environ["PYTHONHTTPSVERIFY"] = "0"

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import kaggle
    print("Downloading DataCo Supply Chain dataset (~7MB)...")
    kaggle.api.dataset_download_files(
        "shashwatwork/dataco-smart-supply-chain-for-big-data",
        path="data/raw/",
        unzip=True
    )
    print("\nFiles downloaded:")
    for f in os.listdir("data/raw/"):
        size_kb = os.path.getsize(f"data/raw/{f}") // 1024
        print(f"  {f}  ({size_kb} KB)")

except Exception as e:
    print(f"\nAuto-download failed: {e}")
    print("\n--- MANUAL DOWNLOAD INSTRUCTIONS ---")
    print("1. Open your browser and go to kaggle.com")
    print("2. Search: DataCo Smart Supply Chain for Big Data")
    print("3. Click the dataset by shashwatwork")
    print("4. Click Download (top right)")
    print("5. Extract the ZIP — find DataCoSupplyChainDataset.csv")
    print(f"6. Move it to: {os.path.abspath(CSV_PATH)}")
