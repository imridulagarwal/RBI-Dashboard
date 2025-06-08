
import os
import sys
import json
from flask import Flask, render_template, jsonify, request
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

app = Flask(__name__)

DB_PATH = os.path.join(os.getcwd(), "rbi_card_stats.db")
DATA_DIR = os.path.join(os.getcwd(), "Processed_Data")
EXCEL_DIR = os.path.join(os.getcwd(), "RBI_ATM_Excel")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXCEL_DIR, exist_ok=True)

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS banks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_name TEXT NOT NULL,
            bank_type TEXT NOT NULL,
            UNIQUE(bank_name)
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            month_str TEXT NOT NULL,
            credit_cards INTEGER NOT NULL DEFAULT 0,
            debit_cards INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (bank_id) REFERENCES banks(id),
            UNIQUE(bank_id, month)
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_time TIMESTAMP NOT NULL,
            update_time TIMESTAMP,
            new_data_available BOOLEAN NOT NULL DEFAULT 0,
            files_added INTEGER NOT NULL DEFAULT 0
        )""")

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

def load_data_from_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        banks_df = pd.read_sql_query("SELECT * FROM banks", conn)
        query = """
        SELECT ms.*, b.bank_name, b.bank_type
        FROM monthly_stats ms
        JOIN banks b ON ms.bank_id = b.id
        """
        stats_df = pd.read_sql_query(query, conn)
        stats_df['month'] = pd.to_datetime(stats_df['month'])

        last_update_query = "SELECT update_time FROM updates WHERE update_time IS NOT NULL ORDER BY update_time DESC LIMIT 1"
        last_update = pd.read_sql_query(last_update_query, conn)
        last_updated = last_update['update_time'].iloc[0] if not last_update.empty else None

        conn.close()

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
    try:
        parser = RBIExcelParser(excel_dir=EXCEL_DIR)
        all_data = parser.process_all_files()
        if not all_data:
            logger.warning("No data processed from Excel files")
            return False

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        conn.execute("BEGIN TRANSACTION")

        records_added = 0
        for df in all_data:
            for _, row in df.iterrows():
                bank_name = row['Bank Name']
                credit_cards = int(row['Credit Cards Outstanding']) if pd.notna(row['Credit Cards Outstanding']) else 0
                debit_cards = int(row['Debit Cards Outstanding']) if pd.notna(row['Debit Cards Outstanding']) else 0
                month = row['Month']
                month_str = row['Month_Str']

                cursor.execute("INSERT OR IGNORE INTO banks (bank_name, bank_type) VALUES (?, ?)", (bank_name, "Unknown"))
                cursor.execute("SELECT id FROM banks WHERE bank_name = ?", (bank_name,))
                bank_id = cursor.fetchone()[0]

                cursor.execute("""
                INSERT OR REPLACE INTO monthly_stats
                (bank_id, month, month_str, credit_cards, debit_cards)
                VALUES (?, ?, ?, ?, ?)
                """, (bank_id, month, month_str, credit_cards, debit_cards))
                records_added += 1

        cursor.execute("""
        INSERT INTO updates (check_time, update_time, new_data_available, files_added)
        VALUES (?, ?, ?, ?)
        """, (datetime.now(), datetime.now(), 1, len(all_data)))

        conn.commit()
        conn.close()

        logger.info(f"Successfully processed and stored {records_added} records")
        return True
    except Exception as e:
        logger.error(f"Error processing and storing Excel files: {str(e)}")
        return False

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    init_db()
    process_and_store_excel_files()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
