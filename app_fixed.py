import os
import sys
import json
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_file
from datetime import datetime
import logging
import pandas as pd
import sqlite3
from update_checker import check_for_updates, download_updates
from excel_parser import RBIExcelParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dashboard.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Database path
DB_PATH = os.path.join(os.getcwd(), "rbi_card_stats.db")

# Data paths
DATA_DIR = os.path.join(os.getcwd(), "Processed_Data")
EXCEL_DIR = os.path.join(os.getcwd(), "RBI_ATM_Excel")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXCEL_DIR, exist_ok=True)

def init_db():
    """Initialize the database with required tables"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create banks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS banks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_name TEXT NOT NULL,
            bank_type TEXT NOT NULL,
            UNIQUE(bank_name)
        )
        ''')
        
        # Create monthly_stats table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            month_str TEXT NOT NULL,
            credit_cards INTEGER NOT NULL DEFAULT 0,
            debit_cards INTEGER NOT NULL DEFAULT 0,
            atm_onsite INTEGER NOT NULL DEFAULT 0,
            atm_offsite INTEGER NOT NULL DEFAULT 0,
            pos_terminals INTEGER NOT NULL DEFAULT 0,
            micro_atms INTEGER NOT NULL DEFAULT 0,
            bharat_qr_codes INTEGER NOT NULL DEFAULT 0,
            upi_qr_codes INTEGER NOT NULL DEFAULT 0,
            pos_txn_volume INTEGER NOT NULL DEFAULT 0,
            pos_txn_value REAL NOT NULL DEFAULT 0,
            online_txn_volume INTEGER NOT NULL DEFAULT 0,
            online_txn_value REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (bank_id) REFERENCES banks(id),
            UNIQUE(bank_id, month)
        )
        ''')
        
        # Create updates table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_time TIMESTAMP NOT NULL,
            update_time TIMESTAMP,
            new_data_available BOOLEAN NOT NULL DEFAULT 0,
            files_added INTEGER NOT NULL DEFAULT 0
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

def load_data_from_db():
    """Load data from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Load banks
        banks_df = pd.read_sql_query("SELECT * FROM banks", conn)
        
        # Load monthly stats
        query = """
        SELECT ms.*, b.bank_name, b.bank_type
        FROM monthly_stats ms
        JOIN banks b ON ms.bank_id = b.id
        """
        stats_df = pd.read_sql_query(query, conn)
        
        # Convert month to datetime
        stats_df['month'] = pd.to_datetime(stats_df['month'])
        
        # Get last update time
        last_update_query = "SELECT update_time FROM updates WHERE update_time IS NOT NULL ORDER BY update_time DESC LIMIT 1"
        last_update = pd.read_sql_query(last_update_query, conn)
        last_updated = last_update['update_time'].iloc[0] if not last_update.empty else None
        
        conn.close()
        
        # Create separate dataframes for credit and debit cards
        credit_card_df = stats_df[['month', 'month_str', 'bank_name', 'bank_type', 'credit_cards']]
        debit_card_df = stats_df[['month', 'month_str', 'bank_name', 'bank_type', 'debit_cards']]
        
        return {
            'all_data': stats_df,
            'credit_card_data': credit_card_df,
            'debit_card_data': debit_card_df,
            'banks': banks_df,
            'last_updated': last_updated
        }
    except Exception as e:
        logger.error(f"Error loading data from database: {str(e)}")
        return None

def process_and_store_excel_files():
    """Process Excel files and store data in the database"""
    try:
        # Initialize parser
  parser = RBIExcelParser(excel_dir=EXCEL_DIR)

        
        # Process all files
        all_data = parser.process_all_files()
        
        if not all_data:
            logger.warning("No data processed from Excel files")
            return False
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Process each record
        records_added = 0
        for record in all_data:
            # Insert or update bank
            cursor.execute(
                "INSERT OR IGNORE INTO banks (bank_name, bank_type) VALUES (?, ?)",
                (record['bank_name'], record['bank_type'])
            )
            
            # Get bank ID
            cursor.execute("SELECT id FROM banks WHERE bank_name = ?", (record['bank_name'],))
            bank_id = cursor.fetchone()[0]
            
            # Format month as string for storage
            month_str = record['month_str']
            month = record['month'].strftime("%Y-%m-%d")
            
            # Insert or update monthly stats
            cursor.execute("""
            INSERT OR REPLACE INTO monthly_stats 
            (bank_id, month, month_str, credit_cards, debit_cards, atm_onsite, atm_offsite, 
            pos_terminals, micro_atms, bharat_qr_codes, upi_qr_codes, pos_txn_volume, 
            pos_txn_value, online_txn_volume, online_txn_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bank_id, month, month_str, record['credit_cards'], record['debit_cards'],
                record['atm_onsite'], record['atm_offsite'], record['pos_terminals'],
                record['micro_atms'], record['bharat_qr_codes'], record['upi_qr_codes'],
                record['pos_txn_volume'], record['pos_txn_value'], record['online_txn_volume'],
                record['online_txn_value']
            ))
            
            records_added += 1
        
        # Record update
        cursor.execute(
            "INSERT INTO updates (check_time, update_time, new_data_available, files_added) VALUES (?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1, len(parser.get_excel_files()))
        )
        
        # Commit transaction
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully processed and stored {records_added} records")
        return True
    except Exception as e:
        logger.error(f"Error processing and storing Excel files: {str(e)}")
        return False

# Global data storage
data = {
    'all_data': None,
    'credit_card_data': None,
    'debit_card_data': None,
    'banks': None,
    'last_updated': None
}

def load_data():
    """Load data from database or process Excel files if needed"""
    global data
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        logger.info("Database does not exist, initializing...")
        init_db()
        
        # Process Excel files
        logger.info("Processing Excel files for initial data load...")
        process_and_store_excel_files()
    
    # Load data from database
    db_data = load_data_from_db()
    
    if db_data:
        data = db_data
        logger.info("Data loaded successfully from database")
        return True
    else:
        logger.error("Failed to load data from database")
        return False

def get_bank_types():
    """Get unique bank types"""
    if data['all_data'] is not None and 'bank_type' in data['all_data'].columns:
        return sorted(data['all_data']['bank_type'].unique().tolist())
    return []

def get_banks_by_type(bank_type=None):
    """Get banks filtered by type"""
    if data['all_data'] is not None:
        if bank_type and bank_type != 'All':
            filtered = data['all_data'][data['all_data']['bank_type'] == bank_type]
            return sorted(filtered['bank_name'].unique().tolist())
        else:
            return sorted(data['all_data']['bank_name'].unique().tolist())
    return []

def get_months():
    """Get available months"""
    if data['all_data'] is not None and 'month_str' in data['all_data'].columns:
        return sorted(data['all_data']['month_str'].unique().tolist())
    return []

def calculate_mom_growth(df, value_col):
    """Calculate month-on-month growth for a specific metric"""
    if df is None or len(df) == 0:
        return pd.DataFrame()
    
    # Sort by month
    df = df.sort_values('month')
    
    # Group by bank and calculate growth
    result = df.copy()
    result['previous'] = result.groupby('bank_name')[value_col].shift(1)
    result['growth'] = ((result[value_col] - result['previous']) / result['previous'] * 100).round(2)
    
    return result

@app.route('/')
def index():
    """Main dashboard page"""
    # Load data if not already loaded
    if data['all_data'] is None:
        load_data()
    
    # Get filter options
    bank_types = get_bank_types()
    months = get_months()
    
    return render_template('index.html', 
                          bank_types=bank_types,
                          months=months,
                          last_updated=data['last_updated'])

@app.route('/api/banks')
def get_banks():
    """API endpoint to get banks based on bank type"""
    bank_type = request.args.get('bank_type', 'All')
    banks = get_banks_by_type(bank_type)
    return jsonify(banks)

@app.route('/api/credit_card_data')
def get_credit_card_data():
    """API endpoint to get credit card data with filters"""
    bank_type = request.args.get('bank_type', 'All')
    bank_name = request.args.get('bank_name', 'All')
    
    if data['credit_card_data'] is None:
        load_data()
    
    df = data['credit_card_data']
    
    # Apply filters
    if bank_type and bank_type != 'All':
        df = df[df['bank_type'] == bank_type]
    
    if bank_name and bank_name != 'All':
        df = df[df['bank_name'] == bank_name]
    
    # Calculate growth if requested
    if request.args.get('include_growth', 'false').lower() == 'true':
        df = calculate_mom_growth(df, 'credit_cards')
    
    # Convert to dict for JSON response
    result = df.to_dict(orient='records')
    return jsonify(result)

@app.route('/api/debit_card_data')
def get_debit_card_data():
    """API endpoint to get debit card data with filters"""
    bank_type = request.args.get('bank_type', 'All')
    bank_name = request.args.get('bank_name', 'All')
    
    if data['debit_card_data'] is None:
        load_data()
    
    df = data['debit_card_data']
    
    # Apply filters
    if bank_type and bank_type != 'All':
        df = df[df['bank_type'] == bank_type]
    
    if bank_name and bank_name != 'All':
        df = df[df['bank_name'] == bank_name]
    
    # Calculate growth if requested
    if request.args.get('include_growth', 'false').lower() == 'true':
        df = calculate_mom_growth(df, 'debit_cards')
    
    # Convert to dict for JSON response
    result = df.to_dict(orient='records')
    return jsonify(result)

@app.route('/api/top_banks')
def get_top_banks():
    """API endpoint to get top banks by credit or debit cards"""
    card_type = request.args.get('card_type', 'credit')
    limit = int(request.args.get('limit', 10))
    
    if data['all_data'] is None:
        load_data()
    
    # Get the latest month data
    latest_month = data['all_data']['month'].max()
    latest_data = data['all_data'][data['all_data']['month'] == latest_month]
    
    # Sort by card count
    if card_type.lower() == 'credit':
        sorted_data = latest_data.sort_values('credit_cards', ascending=False)
        result = sorted_data[['bank_name', 'bank_type', 'credit_cards']].head(limit)
    else:
        sorted_data = latest_data.sort_values('debit_cards', ascending=False)
        result = sorted_data[['bank_name', 'bank_type', 'debit_cards']].head(limit)
    
    return jsonify(result.to_dict(orient='records'))

@app.route('/api/trend_data')
def get_trend_data():
    """API endpoint to get trend data for charts"""
    card_type = request.args.get('card_type', 'credit')
    bank_type = request.args.get('bank_type', 'All')
    
    if data['all_data'] is None:
        load_data()
    
    df = data['all_data']
    
    # Apply bank type filter
    if bank_type and bank_type != 'All':
        df = df[df['bank_type'] == bank_type]
    
    # Group by month and sum
    if card_type.lower() == 'credit':
        monthly_sum = df.groupby('month_str')['credit_cards'].sum().reset_index()
        monthly_sum = monthly_sum.rename(columns={'credit_cards': 'value'})
    else:
        monthly_sum = df.groupby('month_str')['debit_cards'].sum().reset_index()
        monthly_sum = monthly_sum.rename(columns={'debit_cards': 'value'})
    
    # Add card type for reference
    monthly_sum['card_type'] = card_type
    
    return jsonify(monthly_sum.to_dict(orient='records'))

@app.route('/api/comparison_data')
def get_comparison_data():
    """API endpoint to get comparison data between credit and debit cards"""
    bank_name = request.args.get('bank_name', 'All')
    
    if data['all_data'] is None:
        load_data()
    
    df = data['all_data']
    
    # Apply bank filter
    if bank_name and bank_name != 'All':
        df = df[df['bank_name'] == bank_name]
    
    # Group by month
    if bank_name and bank_name != 'All':
        # For single bank, show the actual values
        monthly_data = df[['month_str', 'credit_cards', 'debit_cards']]
    else:
        # For all banks, sum by month
        monthly_data = df.groupby('month_str').agg({
            'credit_cards': 'sum',
            'debit_cards': 'sum'
        }).reset_index()
    
    return jsonify(monthly_data.to_dict(orient='records'))

@app.route('/api/check_updates')
def api_check_updates():
    """API endpoint to check for updates"""
    update_info = check_for_updates()
    
    # Record check in database
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO updates (check_time, new_data_available) VALUES (?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1 if update_info['new_data_available'] else 0)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error recording update check: {str(e)}")
    
    return jsonify(update_info)

@app.route('/api/refresh_data')
def refresh_data():
    """API endpoint to manually refresh data"""
    # Check for updates
    update_info = check_for_updates()
    
    if update_info['new_data_available']:
        # Download new files
        download_result = download_updates()
        
        # Process and store new data
        success = process_and_store_excel_files()
        
        # Reload data
        if success:
            load_data()
    else:
        # Just reload existing data
        success = load_data()
    
    return jsonify({
        'success': success,
        'last_updated': data['last_updated'] if success else None,
        'new_data_available': update_info['new_data_available']
    })

@app.route('/api/export_csv')
def export_csv():
    """API endpoint to export data
(Content truncated due to size limit. Use line ranges to read in chunks) """

@app.route("/cron-update")
def cron_update():
    from update_checker import check_for_updates, download_updates
    check_for_updates()
    download_updates()
    return "✅ Data updated from RBI!"
