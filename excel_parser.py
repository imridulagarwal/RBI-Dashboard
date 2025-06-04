import pandas as pd

class RBIExcelParser:
    def __init__(self, file_path):
        self.file_path = file_path

    def parse(self):
        # Step 1: Load the Excel with no header
        df_raw = pd.read_excel(self.file_path, header=None)

        # Step 2: Find header row with "Bank Name"
        header_row_idx = None
        for i, row in df_raw.iterrows():
            if row.astype(str).str.contains("Bank Name", case=False).any():
                header_row_idx = i
                break
        if header_row_idx is None:
            raise ValueError("Header row with 'Bank Name' not found.")

        # Step 3: Extract next 2 rows for multi-level header (text + metric ID)
        multi_header = df_raw.iloc[header_row_idx:header_row_idx+2].copy()
        multi_header = multi_header.fillna(method='ffill', axis=1).fillna("")

        # Step 4: Combine the two rows into a single row of column names
        combined_header = [
            f"{str(multi_header.iloc[0, i]).strip()}||{str(multi_header.iloc[1, i]).strip()}"
            for i in range(multi_header.shape[1])
        ]

        # Step 5: Read the main data and assign headers
        df = pd.read_excel(self.file_path, header=None, skiprows=header_row_idx + 2)
        df.columns = combined_header

        # Step 6: Find column indices
        bank_col = [col for col in df.columns if "Bank Name" in col][0]
        credit_col = [col for col in df.columns if col.endswith("||7")][0]
        debit_col = [col for col in df.columns if col.endswith("||8")][0]

        # Step 7: Clean output
        output = df[[bank_col, credit_col, debit_col]].copy()
        output.columns = ["Bank Name", "Credit Cards Outstanding", "Debit Cards Outstanding"]
        output = output.dropna(subset=["Bank Name"]).reset_index(drop=True)

        return output
