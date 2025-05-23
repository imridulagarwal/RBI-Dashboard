# RBI ATM/POS/Card Statistics Data Structure Analysis

## Overview
The RBI ATM/POS/Card Statistics page provides monthly data on banking infrastructure and card transactions across Indian banks. The data is organized in a tabular format with multiple categories and metrics.

## Data Structure

### Main Categories
1. **Bank Information**
   - Sr. No.
   - Bank Name
   - Bank Type (Scheduled Commercial Banks, Public Sector Banks, Private Sector Banks)

2. **Infrastructure - Number Outstanding (as on month end)**
   - ATMs & CRMs
     - On-site
     - Off-site
   - PoS
   - Micro ATMs
   - Bharat QR Codes
   - UPI QR Codes
   - Credit Cards
   - Debit Cards

3. **Card Payments Transactions**
   - At PoS
     - Volume (in actuals)
     - Value (in Rs'000)
   - Online (e-com)
     - Volume (in actuals)
     - Value (in Rs'000)

### Data Types
- Most fields are numeric values
- Bank names and categories are text
- Transaction volumes are integers
- Transaction values are in thousands of rupees

### Temporal Aspects
- Data is updated monthly
- Each month's data is available separately
- Some months are marked as "Revised" indicating updates to previously published data

## Database Schema Design Considerations

### Tables
1. **Banks**
   - bank_id (PK)
   - bank_name
   - bank_type (enum: 'Scheduled Commercial', 'Public Sector', 'Private Sector')

2. **Monthly_Statistics**
   - stat_id (PK)
   - bank_id (FK)
   - month (date)
   - is_revised (boolean)
   - atm_onsite (integer)
   - atm_offsite (integer)
   - pos_terminals (integer)
   - micro_atms (integer)
   - bharat_qr_codes (integer)
   - upi_qr_codes (integer)
   - credit_cards (integer)
   - debit_cards (integer)
   - pos_txn_volume (integer)
   - pos_txn_value (decimal)
   - online_txn_volume (integer)
   - online_txn_value (decimal)

### Relationships
- One-to-many relationship between Banks and Monthly_Statistics

## API Requirements

### Endpoints
1. **GET /api/banks**
   - List all banks with their types

2. **GET /api/statistics**
   - Query parameters:
     - month (optional)
     - bank_id (optional)
     - bank_type (optional)
   - Returns statistics based on filters

3. **GET /api/analytics/growth**
   - Query parameters:
     - metric (e.g., 'pos_txn_volume', 'credit_cards')
     - bank_id (optional)
     - start_month
     - end_month
   - Returns month-on-month growth data

## Data Update Mechanism
- Scraper should check for new monthly data periodically
- Handle "Revised" data by updating existing records
- Store historical data for trend analysis
