# RBI ATM/POS/Card Statistics Web Application Requirements

## Backend Requirements

### Database Schema
Based on the data structure analysis, we need a database with the following schema:

```sql
-- Banks table to store bank information
CREATE TABLE banks (
    bank_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_name TEXT NOT NULL,
    bank_type TEXT NOT NULL  -- 'Scheduled Commercial', 'Public Sector', 'Private Sector'
);

-- Monthly statistics table to store all metrics
CREATE TABLE monthly_statistics (
    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id INTEGER NOT NULL,
    month DATE NOT NULL,
    is_revised BOOLEAN DEFAULT FALSE,
    atm_onsite INTEGER,
    atm_offsite INTEGER,
    pos_terminals INTEGER,
    micro_atms INTEGER,
    bharat_qr_codes INTEGER,
    upi_qr_codes INTEGER,
    credit_cards INTEGER,
    debit_cards INTEGER,
    pos_txn_volume INTEGER,
    pos_txn_value DECIMAL(20,2),
    online_txn_volume INTEGER,
    online_txn_value DECIMAL(20,2),
    FOREIGN KEY (bank_id) REFERENCES banks(bank_id)
);

-- Create index for faster queries
CREATE INDEX idx_monthly_statistics_bank_month ON monthly_statistics(bank_id, month);
```

### API Endpoints

1. **Data Retrieval Endpoints**
   - `GET /api/banks` - List all banks with their types
   - `GET /api/bank-types` - Get distinct bank types
   - `GET /api/months` - Get available months in the database
   - `GET /api/statistics` - Get statistics with optional filters:
     - `month` (YYYY-MM format)
     - `bank_id` (integer)
     - `bank_type` (string)
     - `metric` (string, e.g., 'pos_terminals')

2. **Analytics Endpoints**
   - `GET /api/analytics/growth` - Calculate month-on-month growth:
     - `metric` (required, e.g., 'pos_txn_volume')
     - `bank_id` (optional)
     - `bank_type` (optional)
     - `start_month` (optional, defaults to earliest available)
     - `end_month` (optional, defaults to latest available)
   
   - `GET /api/analytics/comparison` - Compare metrics across banks:
     - `metric` (required)
     - `bank_ids` (comma-separated list)
     - `month` (optional)

3. **Data Update Endpoint**
   - `POST /api/admin/update` - Trigger data update (protected endpoint)

### Data Scraper Requirements
- Scheduled task to check for new monthly data
- HTML parsing to extract tabular data from RBI website
- Data transformation and cleaning
- Handling of revised data
- Error logging and notification

### Periodic Update Mechanism
- Configurable update frequency (daily/weekly)
- Automatic detection of new data
- Versioning for revised data
- Update logs

## Frontend Requirements

### UI Components

1. **Dashboard**
   - Summary cards with key metrics
   - Month selector
   - Last updated timestamp

2. **Data Explorer**
   - Interactive data table with:
     - Sorting
     - Filtering by bank, bank type, month
     - Pagination
     - Export to CSV/Excel

3. **Visualization Components**
   - Line charts for time-series data
   - Bar charts for bank comparisons
   - Pie/Donut charts for distribution analysis
   - Heatmaps for correlation visualization

4. **Filter Panel**
   - Date range picker
   - Bank selector (multi-select)
   - Bank type selector
   - Metric selector

5. **Analytics Section**
   - Month-on-month growth calculator
   - Bank comparison tool
   - Trend analysis

### Responsive Design Requirements
- Mobile-first approach
- Responsive layouts for all screen sizes
- Touch-friendly controls
- Optimized data loading for mobile

### User Experience Requirements
- Fast initial load time
- Progressive loading for large datasets
- Clear visual hierarchy
- Consistent color scheme
- Tooltips for data explanation
- Help section with glossary

## Technical Stack

### Backend
- Flask framework
- SQLite for development, PostgreSQL for production
- SQLAlchemy ORM
- APScheduler for periodic tasks
- Beautiful Soup for web scraping

### Frontend
- React.js with TypeScript
- Tailwind CSS for styling
- Recharts for data visualization
- React Query for data fetching
- React Table for data tables

## Deployment Requirements
- Containerized application (Docker)
- CI/CD pipeline
- Automated testing
- Backup strategy for database
- Monitoring and alerting
