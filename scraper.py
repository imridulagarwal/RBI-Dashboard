import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import logging
from src.models.db import db
from src.models.bank import Bank
from src.models.monthly_statistic import MonthlyStatistic
import time

logger = logging.getLogger(__name__)

BASE_URL = "https://www.rbi.org.in/Scripts/ATMView.aspx"

def get_available_months():
    """
    Fetch the list of available months from the RBI website
    Returns a list of tuples (month_name, month_url, is_revised)
    """
    try:
        logger.info(f"Fetching available months from {BASE_URL}")
        response = requests.get(BASE_URL, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        months = []
        
        # Find all month links
        for link in soup.find_all('a'):
            text = link.get_text()
            if "Bank-wise ATM/POS/Card Statistics" in text:
                href = link.get('href')
                if href:
                    # Extract month and year from text
                    match = re.search(r'(\w+)\s+(\d{4})', text)
                    if match:
                        month_name = match.group(1)
                        year = match.group(2)
                        is_revised = "(Revised)" in text
                        
                        # Create a tuple of (month_name, url, is_revised)
                        months.append((f"{month_name} {year}", href, is_revised))
                        logger.info(f"Found month: {month_name} {year}, revised: {is_revised}")
        
        logger.info(f"Found {len(months)} months in total")
        return months
    except Exception as e:
        logger.error(f"Error fetching available months: {str(e)}")
        return []

def parse_month_data(month_url):
    """
    Parse the data for a specific month
    Returns a tuple of (month_date, bank_data_list)
    """
    try:
        # Fix URL joining - ensure proper slash between domain and path
        if not month_url.startswith('http'):
            if month_url.startswith('/'):
                full_url = f"https://www.rbi.org.in{month_url}"
            else:
                full_url = f"https://www.rbi.org.in/Scripts/{month_url}"
        else:
            full_url = month_url
            
        logger.info(f"Parsing data from {full_url}")
        
        # Add delay to avoid overwhelming the server
        time.sleep(2)
        
        response = requests.get(full_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Log the title for debugging
        page_title = soup.title.string if soup.title else "No title found"
        logger.info(f"Page title: {page_title}")
        
        # Extract month and year from page title or URL
        month_date = None
        
        # Try to extract from title first
        if soup.title and soup.title.string:
            title_match = re.search(r'(\w+)\s+(\d{4})', soup.title.string)
            if title_match:
                month_str = title_match.group(1)
                year_str = title_match.group(2)
                try:
                    month_date = datetime.strptime(f"01 {month_str} {year_str}", "%d %B %Y").date()
                    logger.info(f"Extracted month date from title: {month_date}")
                except ValueError:
                    logger.warning(f"Could not parse date from title: {month_str} {year_str}")
        
        # If not found in title, try to extract from URL
        if not month_date and month_url:
            # Extract month ID from URL
            atmid_match = re.search(r'atmid=(\d+)', month_url)
            if atmid_match:
                atmid = atmid_match.group(1)
                logger.info(f"Extracted atmid: {atmid}")
                
                # Map recent atmids to known months (hardcoded fallback)
                atmid_to_month = {
                    '169': (3, 2025),  # March 2025
                    '168': (2, 2025),  # February 2025
                    '167': (1, 2025),  # January 2025
                    '166': (12, 2024), # December 2024
                    '165': (11, 2024), # November 2024
                    '164': (10, 2024), # October 2024
                    '163': (9, 2024),  # September 2024
                    '162': (8, 2024),  # August 2024
                    '161': (7, 2024),  # July 2024
                    '160': (6, 2024),  # June 2024
                }
                
                if atmid in atmid_to_month:
                    month_num, year = atmid_to_month[atmid]
                    month_date = datetime(year, month_num, 1).date()
                    logger.info(f"Mapped atmid {atmid} to date: {month_date}")
        
        # If still no date, use current month as fallback
        if not month_date:
            logger.warning("Could not extract month date, using current month as fallback")
            current_date = datetime.now()
            month_date = datetime(current_date.year, current_date.month, 1).date()
        
        # Find the main data table
        tables = soup.find_all('table')
        main_table = None
        
        # Look for the table with the right structure
        for table in tables:
            if table.find('tr') and len(table.find_all('tr')) > 5:  # Assuming data table has many rows
                main_table = table
                break
        
        if not main_table:
            logger.error(f"Could not find data table in {full_url}")
            return month_date, []
        
        # Process bank data rows
        bank_data = []
        bank_type = None
        
        for row in main_table.find_all('tr')[3:]:  # Skip header rows
            cells = row.find_all('td')
            
            # Skip rows with insufficient data
            if len(cells) < 5:
                continue
            
            # Check if this is a bank type header row
            if len(cells) == 1 or (len(cells) > 1 and not cells[0].get_text().strip().isdigit()):
                bank_type_text = cells[0].get_text().strip()
                if bank_type_text and not bank_type_text.isdigit():
                    bank_type = bank_type_text
                    logger.info(f"Found bank type: {bank_type}")
                continue
            
            try:
                # Extract bank data
                bank_name = cells[1].get_text().strip() if len(cells) > 1 else ""
                
                # Skip rows without a bank name
                if not bank_name:
                    continue
                
                # Create data dictionary with default values
                data = {
                    'bank_type': bank_type,
                    'bank_name': bank_name,
                    'atm_onsite': 0,
                    'atm_offsite': 0,
                    'pos_terminals': 0,
                    'micro_atms': 0,
                    'bharat_qr_codes': 0,
                    'upi_qr_codes': 0,
                    'credit_cards': 0,
                    'debit_cards': 0,
                    'pos_txn_volume': 0,
                    'pos_txn_value': 0,
                    'online_txn_volume': 0,
                    'online_txn_value': 0
                }
                
                # Extract values safely
                if len(cells) > 2:
                    data['atm_onsite'] = parse_int(cells[2].get_text().strip())
                if len(cells) > 3:
                    data['atm_offsite'] = parse_int(cells[3].get_text().strip())
                if len(cells) > 4:
                    data['pos_terminals'] = parse_int(cells[4].get_text().strip())
                if len(cells) > 5:
                    data['micro_atms'] = parse_int(cells[5].get_text().strip())
                if len(cells) > 6:
                    data['bharat_qr_codes'] = parse_int(cells[6].get_text().strip())
                if len(cells) > 7:
                    data['upi_qr_codes'] = parse_int(cells[7].get_text().strip())
                if len(cells) > 8:
                    data['credit_cards'] = parse_int(cells[8].get_text().strip())
                if len(cells) > 9:
                    data['debit_cards'] = parse_int(cells[9].get_text().strip())
                if len(cells) > 10:
                    data['pos_txn_volume'] = parse_int(cells[10].get_text().strip())
                if len(cells) > 11:
                    data['pos_txn_value'] = parse_float(cells[11].get_text().strip())
                if len(cells) > 12:
                    data['online_txn_volume'] = parse_int(cells[12].get_text().strip())
                if len(cells) > 13:
                    data['online_txn_value'] = parse_float(cells[13].get_text().strip())
                
                bank_data.append(data)
                logger.info(f"Parsed data for bank: {bank_name}")
            except Exception as e:
                logger.warning(f"Error parsing row data for {bank_name if 'bank_name' in locals() else 'unknown bank'}: {str(e)}")
                continue
        
        logger.info(f"Parsed {len(bank_data)} bank records for {month_date}")
        return month_date, bank_data
    
    except Exception as e:
        logger.error(f"Error parsing month data: {str(e)}")
        return None, []

def parse_int(value):
    """Safely parse integer values from text"""
    try:
        if not value:
            return 0
        # Remove commas and other non-numeric characters
        clean_value = re.sub(r'[^\d.-]', '', value)
        return int(float(clean_value)) if clean_value else 0
    except (ValueError, TypeError):
        return 0

def parse_float(value):
    """Safely parse float values from text"""
    try:
        if not value:
            return 0.0
        # Remove commas and other non-numeric characters
        clean_value = re.sub(r'[^\d.-]', '', value)
        return float(clean_value) if clean_value else 0.0
    except (ValueError, TypeError):
        return 0.0

def update_database(month_date, bank_data, is_revised):
    """
    Update the database with the parsed data
    """
    try:
        logger.info(f"Updating database with {len(bank_data)} records for {month_date}")
        
        # Process each bank
        for data in bank_data:
            # Find or create bank
            bank = Bank.query.filter_by(bank_name=data['bank_name']).first()
            if not bank:
                bank = Bank(
                    bank_name=data['bank_name'],
                    bank_type=data['bank_type'] or "Unknown"
                )
                db.session.add(bank)
                db.session.flush()  # Get the bank_id without committing
                logger.info(f"Created new bank: {data['bank_name']}")
            
            # Find existing statistic for this bank and month
            stat = MonthlyStatistic.query.filter_by(
                bank_id=bank.bank_id,
                month=month_date
            ).first()
            
            # If statistic exists and is not revised, or if it's a new entry
            if not stat or (is_revised and not stat.is_revised):
                if stat:
                    # Update existing record if it's being revised
                    logger.info(f"Updating existing record for {data['bank_name']} ({month_date})")
                    stat.is_revised = True
                    stat.atm_onsite = data['atm_onsite']
                    stat.atm_offsite = data['atm_offsite']
                    stat.pos_terminals = data['pos_terminals']
                    stat.micro_atms = data['micro_atms']
                    stat.bharat_qr_codes = data['bharat_qr_codes']
                    stat.upi_qr_codes = data['upi_qr_codes']
                    stat.credit_cards = data['credit_cards']
                    stat.debit_cards = data['debit_cards']
                    stat.pos_txn_volume = data['pos_txn_volume']
                    stat.pos_txn_value = data['pos_txn_value']
                    stat.online_txn_volume = data['online_txn_volume']
                    stat.online_txn_value = data['online_txn_value']
                else:
                    # Create new record
                    logger.info(f"Creating new record for {data['bank_name']} ({month_date})")
                    stat = MonthlyStatistic(
                        bank_id=bank.bank_id,
                        month=month_date,
                        is_revised=is_revised,
                        atm_onsite=data['atm_onsite'],
                        atm_offsite=data['atm_offsite'],
                        pos_terminals=data['pos_terminals'],
                        micro_atms=data['micro_atms'],
                        bharat_qr_codes=data['bharat_qr_codes'],
                        upi_qr_codes=data['upi_qr_codes'],
                        credit_cards=data['credit_cards'],
                        debit_cards=data['debit_cards'],
                        pos_txn_volume=data['pos_txn_volume'],
                        pos_txn_value=data['pos_txn_value'],
                        online_txn_volume=data['online_txn_volume'],
                        online_txn_value=data['online_txn_value']
                    )
                    db.session.add(stat)
        
        # Commit all changes
        db.session.commit()
        logger.info(f"Successfully updated database for {month_date}")
        return True
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating database: {str(e)}")
        return False

def check_for_updates(app):
    """
    Check for new data and update the database
    This function is called by the scheduler
    """
    with app.app_context():
        try:
            logger.info("Starting RBI data update process")
            
            # Get available months
            months = get_available_months()
            if not months:
                logger.warning("No months found on RBI website")
                return
            
            logger.info(f"Found {len(months)} months on RBI website")
            
            # Process each month
            for month_name, month_url, is_revised in months:
                logger.info(f"Processing {month_name} (Revised: {is_revised})")
                
                # Parse month data
                month_date, bank_data = parse_month_data(month_url)
                if not month_date or not bank_data:
                    logger.warning(f"No data found for {month_name}")
                    continue
                
                # Update database
                success = update_database(month_date, bank_data, is_revised)
                if success:
                    logger.info(f"Successfully updated data for {month_name}")
                else:
                    logger.error(f"Failed to update data for {month_name}")
            
            logger.info("RBI data update process completed")
        
        except Exception as e:
            logger.error(f"Error in RBI data update process: {str(e)}")

def force_update(app):
    """
    Force an immediate update of the database
    This function can be called manually
    """
    logger.info("Forcing immediate RBI data update")
    check_for_updates(app)
    return True
