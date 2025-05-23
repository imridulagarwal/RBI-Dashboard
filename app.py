import os
import pandas as pd
import json
from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime
import logging

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

# Data paths
DATA_DIR = os.path.join(os.getcwd(), "Processed_Data")
ALL_DATA_PATH = os.path.join(DATA_DIR, "all_rbi_data.csv")
CREDIT_CARD_PATH = os.path.join(DATA_DIR, "credit_card_data.csv")
DEBIT_CARD_PATH = os.path.join(DATA_DIR, "debit_card_data.csv")
BANK_TYPES_PATH = os.path.join(DATA_DIR, "bank_types.csv")

# Global data storage
data = {
    'all_data': None,
    'credit_card_data': None,
    'debit_card_data': None,
    'bank_types': None,
    'last_updated': None
}

def load_data():
    """Load all data from CSV files"""
    try:
        # Load all datasets
        data['all_data'] = pd.read_csv(ALL_DATA_PATH)
        data['credit_card_data'] = pd.read_csv(CREDIT_CARD_PATH)
        data['debit_card_data'] = pd.read_csv(DEBIT_CARD_PATH)
        data['bank_types'] = pd.read_csv(BANK_TYPES_PATH)
        
        # Convert month column to datetime
        if 'month' in data['all_data'].columns:
            data['all_data']['month'] = pd.to_datetime(data['all_data']['month'])
        if 'month' in data['credit_card_data'].columns:
            data['credit_card_data']['month'] = pd.to_datetime(data['credit_card_data']['month'])
        if 'month' in data['debit_card_data'].columns:
            data['debit_card_data']['month'] = pd.to_datetime(data['debit_card_data']['month'])
        
        # Set last updated timestamp
        data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info("Data loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
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

def check_for_updates():
    """Check if new data is available from RBI website"""
    # In a real implementation, this would check the RBI website for new data
    # Since scheduled tasks are disabled, this is a manual check
    
    # For demonstration, we'll just return the last update time
    return {
        'new_data_available': False,
        'last_checked': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'last_updated': data['last_updated']
    }

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
    return jsonify(update_info)

@app.route('/api/refresh_data')
def refresh_data():
    """API endpoint to manually refresh data"""
    success = load_data()
    return jsonify({
        'success': success,
        'last_updated': data['last_updated'] if success else None
    })

if __name__ == '__main__':
    # Load data on startup
    load_data()
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)
