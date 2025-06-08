# ✅ Updated `parser.py`

import pandas as pd
import os
import re
from datetime import datetime

class RBIExcelParser:
    def __init__(self, excel_dir):
        self.excel_dir = excel_dir

    def process_all_files(self):
        all_data = []
        for file_name in os.listdir(self.excel_dir):
            if file_name.endswith(".xlsx"):
                file_path = os.path.join(self.excel_dir, file_name)
                try:
                    df = self.parse_excel(file_path)
                    month_str = self.extract_month_from_filename(file_name)
                    df["month_str"] = month_str
                    df["month"] = self.convert_month_to_date(month_str)
                    df["bank_type"] = "Scheduled Commercial Bank"  # Fallback value; can update

                    # Rename for consistency with DB fields
                    df = df.rename(columns={
                        "Bank Name": "bank_name",
                        "Credit Cards Outstanding": "credit_cards",
                        "Debit Cards Outstanding": "debit_cards"
                    })

                    # Add other fields with 0 default
                    df["atm_onsite"] = 0
                    df["atm_offsite"] = 0
                    df["pos_terminals"] = 0
                    df["micro_atms"] = 0
                    df["bharat_qr_codes"] = 0
                    df["upi_qr_codes"] = 0
                    df["pos_txn_volume"] = 0
                    df["pos_txn_value"] = 0
                    df["online_txn_volume"] = 0
                    df["online_txn_value"] = 0

                    all_data.extend(df.to_dict(orient="records"))
                except Exception as e:
                    print(f"❌ Error parsing {file_name}: {e}")
        return all_data

    def parse_excel(self, file_path):
        # Step 1: Preview to find header row
        preview = pd.read_excel(file_path, header=None, nrows=10)
        header_row_idx = None
        for i in range(len(preview)):
            if preview.iloc[i].astype(str).str.contains("Bank Name", case=False).any():
                header_row_idx = i
                break
        if header_row_idx is None:
            raise ValueError("❌ Could not find header row with 'Bank Name'")

        # Step 2: Read 3 rows for header
        header_rows = pd.read_excel(file_path, header=None, skiprows=header_row_idx, nrows=3)
        multi_header = header_rows.ffill(axis=1).astype(str)
        combined_header = multi_header.apply(lambda x: ' '.join(x).strip().lower(), axis=0)

        # Step 3: Read actual data
        df = pd.read_excel(file_path, header=None, skiprows=header_row_idx + 3)

        # Step 4: Fix headers if mismatched
        if len(combined_header) > len(df.columns):
            combined_header = combined_header[:len(df.columns)]
        elif len(combined_header) < len(df.columns):
            combined_header = combined_header.tolist() + [f"extra_col_{i}" for i in range(len(df.columns) - len(combined_header))]

        df.columns = combined_header

        # Step 5: Identify columns
        bank_col = [col for col in df.columns if "bank name" in col][0]
        credit_col = [col for col in df.columns if "credit card" in col][0]
        debit_col = [col for col in df.columns if "debit card" in col][0]

        df_filtered = df[[bank_col, credit_col, debit_col]].dropna(subset=[bank_col])
        df_filtered.columns = ["Bank Name", "Credit Cards Outstanding", "Debit Cards Outstanding"]
        df_filtered = df_filtered.reset_index(drop=True)

        return df_filtered

    def extract_month_from_filename(self, filename):
        match = re.search(r"ATM([A-Z]+)(\d{4})", filename)
        if match:
            month_name = match.group(1).capitalize()
            year = match.group(2)
            return f"{month_name}-{year}"
        return "Unknown"

    def convert_month_to_date(self, month_str):
        try:
            return datetime.strptime(month_str, "%B-%Y")
        except:
            return datetime.now()
