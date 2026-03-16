import pandas as pd
import sys

try:
    df = pd.read_excel(r'C:\Users\Matthew Reyes\Documents\ronalds\inventario.xlsx', sheet_name=None)
    for k, v in df.items():
        print(f"--- Sheet: {k} ---")
        print(v.head().to_markdown())
        print("\n")
except Exception as e:
    print(f"Error: {e}")
