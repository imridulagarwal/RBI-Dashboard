import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from src.models.db import db
from src.models.bank import Bank
from src.models.monthly_statistic import MonthlyStatistic
from src.main import create_app
import random

# Sample bank types
BANK_TYPES = [
    "Public Sector Banks",
    "Private Sector Banks",
    "Foreign Banks",
    "Small Finance Banks",
    "Payment Banks"
]

# Sample bank names
BANK_NAMES = {
    "Public Sector Banks": [
        "State Bank of India", "Bank of Baroda", "Punjab National Bank", 
        "Canara Bank", "Union Bank of India", "Bank of India", "Indian Bank"
    ],
    "Private Sector Banks": [
        "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank", 
        "IndusInd Bank", "Yes Bank", "IDFC First Bank", "Federal Bank"
    ],
    "Foreign Banks": [
        "Standard Chartered Bank", "Citibank", "HSBC Bank", "Deutsche Bank",
        "DBS Bank", "Barclays Bank"
    ],
    "Small Finance Banks": [
        "AU Small Finance Bank", "Equitas Small Finance Bank", "Ujjivan Small Finance Bank",
        "Jana Small Finance Bank", "Suryoday Small Finance Bank"
    ],
    "Payment Banks": [
        "Paytm Payments Bank", "Airtel Payments Bank", "India Post Payments Bank",
        "Fino Payments Bank", "Jio Payments Bank"
    ]
}

def generate_sample_data():
    """Generate sample data for the RBI ATM/POS/Card Statistics dashboard"""
    app = create_app()
    
    with app.app_context():
        print("Generating sample data...")
        
        # Clear existing data
        MonthlyStatistic.query.delete()
        Bank.query.delete()
        
        # Create banks
        banks = []
        for bank_type in BANK_TYPES:
            for bank_name in BANK_NAMES[bank_type]:
                bank = Bank(
                    bank_name=bank_name,
                    bank_type=bank_type
                )
                db.session.add(bank)
                banks.append(bank)
        
        db.session.commit()
        print(f"Created {len(banks)} banks")
        
        # Generate monthly statistics for the past 12 months
        today = datetime.now()
        months = []
        for i in range(12):
            month_date = datetime(today.year, today.month, 1) - timedelta(days=30*i)
            months.append(month_date)
        
        # Create statistics for each bank and month
        stats_count = 0
        for bank in banks:
            for month in months:
                # Base values that grow over time
                base_atm_onsite = random.randint(1000, 5000) if bank.bank_type in ["Public Sector Banks", "Private Sector Banks"] else random.randint(100, 1000)
                base_atm_offsite = random.randint(500, 3000) if bank.bank_type in ["Public Sector Banks", "Private Sector Banks"] else random.randint(50, 500)
                base_pos = random.randint(10000, 100000) if bank.bank_type in ["Public Sector Banks", "Private Sector Banks"] else random.randint(1000, 10000)
                base_credit_cards = random.randint(100000, 1000000) if bank.bank_type in ["Private Sector Banks", "Foreign Banks"] else random.randint(10000, 100000)
                base_debit_cards = random.randint(1000000, 10000000) if bank.bank_type in ["Public Sector Banks", "Private Sector Banks"] else random.randint(100000, 1000000)
                
                # Growth factor based on month (more recent months have higher values)
                growth_factor = 1 + (months.index(month) * 0.02)
                
                # Add some randomness for month-to-month variation
                random_factor = random.uniform(0.95, 1.05)
                
                # Calculate values with growth and randomness
                atm_onsite = int(base_atm_onsite * growth_factor * random_factor)
                atm_offsite = int(base_atm_offsite * growth_factor * random_factor)
                pos_terminals = int(base_pos * growth_factor * random_factor)
                micro_atms = int(atm_onsite * 0.2 * random_factor)
                bharat_qr_codes = int(pos_terminals * 0.3 * random_factor)
                upi_qr_codes = int(pos_terminals * 0.5 * random_factor)
                credit_cards = int(base_credit_cards * growth_factor * random_factor)
                debit_cards = int(base_debit_cards * growth_factor * random_factor)
                
                # Transaction volumes and values
                pos_txn_volume = int(pos_terminals * random.randint(50, 200) * growth_factor)
                pos_txn_value = pos_txn_volume * random.randint(1000, 5000)
                online_txn_volume = int((credit_cards + debit_cards) * 0.1 * growth_factor * random_factor)
                online_txn_value = online_txn_volume * random.randint(2000, 10000)
                
                # Create statistic
                stat = MonthlyStatistic(
                    bank_id=bank.bank_id,
                    month=month,
                    is_revised=False,
                    atm_onsite=atm_onsite,
                    atm_offsite=atm_offsite,
                    pos_terminals=pos_terminals,
                    micro_atms=micro_atms,
                    bharat_qr_codes=bharat_qr_codes,
                    upi_qr_codes=upi_qr_codes,
                    credit_cards=credit_cards,
                    debit_cards=debit_cards,
                    pos_txn_volume=pos_txn_volume,
                    pos_txn_value=pos_txn_value,
                    online_txn_volume=online_txn_volume,
                    online_txn_value=online_txn_value
                )
                db.session.add(stat)
                stats_count += 1
                
                # Add some revised data for random months
                if random.random() < 0.1:  # 10% chance of revision
                    revised_stat = MonthlyStatistic(
                        bank_id=bank.bank_id,
                        month=month,
                        is_revised=True,
                        atm_onsite=int(atm_onsite * random.uniform(0.95, 1.05)),
                        atm_offsite=int(atm_offsite * random.uniform(0.95, 1.05)),
                        pos_terminals=int(pos_terminals * random.uniform(0.95, 1.05)),
                        micro_atms=int(micro_atms * random.uniform(0.95, 1.05)),
                        bharat_qr_codes=int(bharat_qr_codes * random.uniform(0.95, 1.05)),
                        upi_qr_codes=int(upi_qr_codes * random.uniform(0.95, 1.05)),
                        credit_cards=int(credit_cards * random.uniform(0.95, 1.05)),
                        debit_cards=int(debit_cards * random.uniform(0.95, 1.05)),
                        pos_txn_volume=int(pos_txn_volume * random.uniform(0.95, 1.05)),
                        pos_txn_value=int(pos_txn_value * random.uniform(0.95, 1.05)),
                        online_txn_volume=int(online_txn_volume * random.uniform(0.95, 1.05)),
                        online_txn_value=int(online_txn_value * random.uniform(0.95, 1.05))
                    )
                    db.session.add(revised_stat)
                    stats_count += 1
        
        db.session.commit()
        print(f"Created {stats_count} monthly statistics records")
        print("Sample data generation complete!")

if __name__ == "__main__":
    generate_sample_data()
