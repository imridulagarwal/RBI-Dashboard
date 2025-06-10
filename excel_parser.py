import os
import pandas as pd
import re
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('excel_parser.log')
    ]
)
logger = logging.getLogger(__name__)

class RBIExcelParser:
    """
    Parser for RBI ATM/POS/Card Statistics Excel files
    Handles merged cells and normalizes bank names across different files
    """
    
    def __init__(self, excel_dir="RBI_ATM_Excel"):
        """Initialize the parser with the directory containing Excel files"""
        self.excel_dir = excel_dir
        self.bank_name_mapping = {}  # For normalizing bank names
        self.processed_data = []
        self.bank_types = set()
        
        # Create output directory
        self.output_dir = os.path.join(os.getcwd(), "Processed_Data")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_excel_files(self):
        """Get all Excel files in the directory"""
        excel_files = []
        for file in os.listdir(self.excel_dir):
            if file.lower().endswith(('.xls', '.xlsx')):
                excel_files.append(os.path.join(self.excel_dir, file))
        return sorted(excel_files)
    
    def extract_date_from_filename(self, filename):
        """Extract month and year from filename"""
        # Extract month name and year using regex (handles 2 or 4 digit years)
        match = re.search(r'ATM([A-Za-z]+)(\d{2,4})', os.path.basename(filename))
        if match:
            month_name = match.group(1)
            year_str = match.group(2)

            # Convert 2 digit year to 4 digit year
            if len(year_str) == 2:
                year = int(year_str)
                year += 2000 if year < 100 else 0
            else:
                year = int(year_str)
            
            # Convert month name to number
            try:
                month_date = datetime.strptime(f"01 {month_name} {year}", "%d %B %Y")
                return month_date
            except ValueError:
                logger.warning(f"Could not parse date from filename: {filename}")
        
        # Fallback: use file modification time
        file_mtime = os.path.getmtime(filename)
        return datetime.fromtimestamp(file_mtime)
    
    def normalize_bank_name(self, bank_name):
        """Normalize bank names to handle variations across files"""
        if not bank_name or not isinstance(bank_name, str):
            return "Unknown Bank"
            
        # Remove extra spaces and convert to uppercase for comparison
        clean_name = re.sub(r'\s+', ' ', bank_name).strip().upper()
        
        # Check if we already have a mapping for this name
        if clean_name in self.bank_name_mapping:
            return self.bank_name_mapping[clean_name]
        
        # Common variations to normalize
        if "SBI" in clean_name or "STATE BANK OF INDIA" in clean_name:
            normalized = "STATE BANK OF INDIA"
        elif "HDFC" in clean_name:
            normalized = "HDFC BANK LTD"
        elif "ICICI" in clean_name:
            normalized = "ICICI BANK LTD"
        elif "AXIS" in clean_name:
            normalized = "AXIS BANK LTD"
        elif "PNB" in clean_name or "PUNJAB NATIONAL" in clean_name:
            normalized = "PUNJAB NATIONAL BANK"
        elif "BOB" in clean_name or "BANK OF BARODA" in clean_name:
            normalized = "BANK OF BARODA"
        elif "BOI" in clean_name or "BANK OF INDIA" in clean_name:
            normalized = "BANK OF INDIA"
        elif "CANARA" in clean_name:
            normalized = "CANARA BANK"
        elif "UNION BANK" in clean_name:
            normalized = "UNION BANK OF INDIA"
        elif "INDIAN BANK" in clean_name:
            normalized = "INDIAN BANK"
        elif "KOTAK" in clean_name:
            normalized = "KOTAK MAHINDRA BANK LTD"
        elif "IDFC" in clean_name:
            normalized = "IDFC FIRST BANK LTD"
        elif "YES" in clean_name:
            normalized = "YES BANK LTD"
        elif "INDUSIND" in clean_name:
            normalized = "INDUSIND BANK LTD"
        elif "FEDERAL" in clean_name:
            normalized = "FEDERAL BANK LTD"
        elif "RBL" in clean_name:
            normalized = "RBL BANK LTD"
        elif "IDBI" in clean_name:
            normalized = "IDBI BANK LTD"
        elif "CITI" in clean_name:
            normalized = "CITI BANK"
        elif "HSBC" in clean_name:
            normalized = "HSBC LTD"
        elif "STANDARD CHARTERED" in clean_name:
            normalized = "STANDARD CHARTERED BANK LTD"
        elif "DBS" in clean_name:
            normalized = "DBS INDIA BANK LTD"
        elif "DEUTSCHE" in clean_name:
            normalized = "DEUTSCHE BANK LTD"
        elif "BARCLAYS" in clean_name:
            normalized = "BARCLAYS BANK PLC"
        elif "AMERICAN EXPRESS" in clean_name:
            normalized = "AMERICAN EXPRESS BANKING CORPORATION"
        elif "PAYTM" in clean_name:
            normalized = "PAYTM PAYMENTS BANK"
        elif "AIRTEL" in clean_name:
            normalized = "AIRTEL PAYMENTS BANK"
        elif "INDIA POST" in clean_name:
            normalized = "INDIA POST PAYMENTS BANK"
        elif "FINO" in clean_name:
            normalized = "FINO PAYMENTS BANK"
        elif "JIO" in clean_name:
            normalized = "JIO PAYMENTS BANK"
        elif "AU" in clean_name:
            normalized = "AU SMALL FINANCE BANK LTD"
        elif "EQUITAS" in clean_name:
            normalized = "EQUITAS SMALL FINANCE BANK LTD"
        elif "UJJIVAN" in clean_name:
            normalized = "UJJIVAN SMALL FINANCE BANK LTD"
        elif "JANA" in clean_name:
            normalized = "JANA SMALL FINANCE BANK LTD"
        elif "SURYODAY" in clean_name:
            normalized = "SURYODAY SMALL FINANCE BANK LTD"
        else:
            # Keep original name if no specific rule matches
            normalized = bank_name.strip()
        
        # Store the mapping for future use
        self.bank_name_mapping[clean_name] = normalized
        return normalized
    
    def determine_bank_type(self, bank_name, row_idx, df):
        """Determine bank type based on position in the Excel file or bank name"""
        # Try to find bank type from previous rows
        for i in range(row_idx, max(0, row_idx-10), -1):
            if i in df.index:
                cell_value = df.iloc[i, 0]
                if isinstance(cell_value, str) and cell_value.strip():
                    # Check if this looks like a bank type header
                    if any(keyword in cell_value.upper() for keyword in ["BANK", "PUBLIC", "PRIVATE", "FOREIGN", "PAYMENT", "SMALL FINANCE"]):
                        return cell_value.strip()
        
        # If not found, infer from bank name
        bank_name_upper = bank_name.upper()
        if "PAYMENT" in bank_name_upper:
            return "Payment Banks"
        elif "SMALL FINANCE" in bank_name_upper:
            return "Small Finance Banks"
        elif any(foreign_bank in bank_name_upper for foreign_bank in ["CITI", "HSBC", "STANDARD CHARTERED", "DBS", "DEUTSCHE", "BARCLAYS", "AMERICAN EXPRESS"]):
            return "Foreign Banks"
        elif any(public_bank in bank_name_upper for public_bank in ["STATE BANK OF INDIA", "BANK OF BARODA", "PUNJAB NATIONAL", "CANARA", "UNION BANK OF INDIA", "BANK OF INDIA", "INDIAN BANK"]):
            return "Public Sector Banks"
        else:
            return "Private Sector Banks"
    
    def process_excel_file(self, file_path):
        """Process a single Excel file, handling merged cells and extracting data"""
        logger.info(f"Processing file: {file_path}")
        
        # Extract date from filename
        file_date = self.extract_date_from_filename(file_path)
        month_year = file_date.strftime("%B %Y")
        logger.info(f"Extracted date: {month_year}")
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path, header=None)
            
            # Find the main data section
            data_rows = []
            current_bank_type = None
            
            # Iterate through rows to find and process data
            for idx, row in df.iterrows():
                # Skip empty rows
                if row.isna().all():
                    continue
                
                # Check if this is a bank type header row
                first_cell = str(row.iloc[0]).strip() if not pd.isna(row.iloc[0]) else ""
                if first_cell and not first_cell.isdigit() and any(keyword in first_cell.upper() for keyword in ["BANK", "PUBLIC", "PRIVATE", "FOREIGN", "PAYMENT", "SMALL FINANCE"]):
                    current_bank_type = first_cell
                    self.bank_types.add(current_bank_type)
                    logger.info(f"Found bank type: {current_bank_type}")
                    continue
                
                # Check if this is a data row (usually starts with a number or has a bank name in column 1)
                bank_name_col = 1  # Usually bank names are in column 1 (0-indexed)
                if bank_name_col < len(row) and not pd.isna(row.iloc[bank_name_col]) and isinstance(row.iloc[bank_name_col], str):
                    bank_name = row.iloc[bank_name_col].strip()
                    
                    # Skip if this doesn't look like a bank name
                    if not bank_name or len(bank_name) < 3:
                        continue
                    
                    # Normalize bank name
                    normalized_bank_name = self.normalize_bank_name(bank_name)
                    
                    # Determine bank type if not already set
                    if not current_bank_type:
                        current_bank_type = self.determine_bank_type(normalized_bank_name, idx, df)
                    
                    # Extract data fields
                    # The column positions may vary, so we'll try to be flexible
                    data_row = {
                        'month': file_date,
                        'month_str': month_year,
                        'bank_name': normalized_bank_name,
                        'bank_type': current_bank_type,
                        'atm_onsite': self.safe_extract_numeric(row, 2),
                        'atm_offsite': self.safe_extract_numeric(row, 3),
                        'pos_terminals': self.safe_extract_numeric(row, 4),
                        'micro_atms': self.safe_extract_numeric(row, 5),
                        'bharat_qr_codes': self.safe_extract_numeric(row, 6),
                        'upi_qr_codes': self.safe_extract_numeric(row, 7),
                        'credit_cards': self.safe_extract_numeric(row, 8),
                        'debit_cards': self.safe_extract_numeric(row, 9),
                        'pos_txn_volume': self.safe_extract_numeric(row, 10),
                        'pos_txn_value': self.safe_extract_numeric(row, 11),
                        'online_txn_volume': self.safe_extract_numeric(row, 12),
                        'online_txn_value': self.safe_extract_numeric(row, 13)
                    }
                    
                    data_rows.append(data_row)
                    logger.debug(f"Extracted data for bank: {normalized_bank_name}")
            
            logger.info(f"Extracted {len(data_rows)} bank records from {file_path}")
            return data_rows
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return []
    
    def safe_extract_numeric(self, row, col_idx):
        """Safely extract numeric value from DataFrame row"""
        if col_idx >= len(row) or pd.isna(row.iloc[col_idx]):
            return 0
        
        value = row.iloc[col_idx]
        
        # If already numeric, return as is
        if isinstance(value, (int, float)):
            return value
        
        # Try to convert string to numeric
        if isinstance(value, str):
            # Remove commas, spaces, and other non-numeric characters
            clean_value = re.sub(r'[^\d.-]', '', value)
            try:
                return float(clean_value) if clean_value else 0
            except (ValueError, TypeError):
                return 0
        
        return 0
    
    def process_all_files(self):
        """Process all Excel files in the directory"""
        excel_files = self.get_excel_files()
        logger.info(f"Found {len(excel_files)} Excel files to process")
        
        all_data = []
        for file_path in excel_files:
            file_data = self.process_excel_file(file_path)
            all_data.extend(file_data)
        
        self.processed_data = all_data
        logger.info(f"Processed {len(all_data)} total records from all files")
        
        return all_data
    
    def save_processed_data(self):
        """Save processed data to CSV files"""
        if not self.processed_data:
            logger.warning("No processed data to save")
            return
        
        # Save all data to a single CSV
        all_data_df = pd.DataFrame(self.processed_data)
        all_data_path = os.path.join(self.output_dir, "all_rbi_data.csv")
        all_data_df.to_csv(all_data_path, index=False)
        logger.info(f"Saved all data to {all_data_path}")
        
        # Save credit card data
        credit_card_df = all_data_df[['month', 'month_str', 'bank_name', 'bank_type', 'credit_cards']]
        credit_card_path = os.path.join(self.output_dir, "credit_card_data.csv")
        credit_card_df.to_csv(credit_card_path, index=False)
        logger.info(f"Saved credit card data to {credit_card_path}")
        
        # Save debit card data
        debit_card_df = all_data_df[['month', 'month_str', 'bank_name', 'bank_type', 'debit_cards']]
        debit_card_path = os.path.join(self.output_dir, "debit_card_data.csv")
        debit_card_df.to_csv(debit_card_path, index=False)
        logger.info(f"Saved debit card data to {debit_card_path}")
        
        # Save bank type mapping
        bank_types_df = pd.DataFrame({
            'bank_name': list(self.bank_name_mapping.values()),
            'bank_type': [self.determine_bank_type(bank, 0, pd.DataFrame()) for bank in self.bank_name_mapping.values()]
        })
        bank_types_path = os.path.join(self.output_dir, "bank_types.csv")
        bank_types_df.to_csv(bank_types_path, index=False)
        logger.info(f"Saved bank type mapping to {bank_types_path}")
        
        return {
            'all_data': all_data_path,
            'credit_card_data': credit_card_path,
            'debit_card_data': debit_card_path,
            'bank_types': bank_types_path
        }

if __name__ == "__main__":
    parser = RBIExcelParser()
    parser.process_all_files()
    output_files = parser.save_processed_data()
    
    print("\nProcessing complete!")
    print(f"Total records processed: {len(parser.processed_data)}")
    print(f"Unique banks identified: {len(parser.bank_name_mapping)}")
    print(f"Bank types identified: {len(parser.bank_types)}")
    print("\nOutput files:")
    for key, path in output_files.items():
        print(f"- {key}: {path}")
