import pandas as pd

def parse_rbi_excel(file_path):
    # Step 1: Read initial rows to detect header row
    preview = pd.read_excel(file_path, header=None, nrows=10)
    header_row_idx = None
    for i in range(len(preview)):
        if preview.iloc[i].astype(str).str.contains("Bank Name", case=False).any():
            header_row_idx = i
            break

    if header_row_idx is None:
        raise ValueError("❌ Could not find header row with 'Bank Name'")

    # Step 2: Read next 3 rows to build the header
    header_rows = pd.read_excel(file_path, header=None, skiprows=header_row_idx, nrows=3)
    multi_header = header_rows.ffill(axis=1).astype(str)
    combined_header = multi_header.apply(lambda x: ' '.join(x).strip().lower(), axis=0)

    # Step 3: Read the full data below header
    df = pd.read_excel(file_path, header=None, skiprows=header_row_idx + 3)

    # Step 4: Align header count
    if len(combined_header) > len(df.columns):
        combined_header = combined_header[:len(df.columns)]
    elif len(combined_header) < len(df.columns):
        combined_header = combined_header.tolist() + [f"extra_col_{i}" for i in range(len(df.columns) - len(combined_header))]

    df.columns = combined_header

    # Step 5: Detect relevant columns by partial match
    bank_col = next((col for col in df.columns if "bank name" in col), None)
    credit_col = next((col for col in df.columns if "credit card" in col), None)
    debit_col = next((col for col in df.columns if "debit card" in col), None)

    if not all([bank_col, credit_col, debit_col]):
        raise ValueError("❌ Required columns not found in the Excel file.")

    # Step 6: Extract and clean data
    df_filtered = df[[bank_col, credit_col, debit_col]].dropna(subset=[bank_col])
    df_filtered.columns = ["Bank Name", "Credit Cards Outstanding", "Debit Cards Outstanding"]
    df_filtered = df_filtered.reset_index(drop=True)

    return df_filtered
