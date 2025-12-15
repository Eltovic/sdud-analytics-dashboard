# Data Files

## Source Data
The source data file `Raw/sdud-2025-updated-dec2025.csv` (238 MB) is not included in this repository due to GitHub's file size limits.

### Data Structure
- **Records**: 100,000+ Medicaid pharmacy claims
- **Coverage**: 52 states, multiple years/quarters, 2 utilization types
- **Key Columns**: state, year, quarter, product_name, utilization_type, number_of_prescriptions, units_reimbursed, total_amount_reimbursed, medicaid_amount_reimbursed, is_suppressed

### Data Source
The data is derived from the CMS State Drug Utilization Data (SDUD) available at:
- https://data.medicaid.gov/datasets?q=state%20drug%20utilization

### To Use This Project
1. Download SDUD data from CMS (or use your own similar dataset)
2. Place the CSV in the `Raw/` directory
3. Update the file path in `scripts/04_phase3_eda_kpis.py` if needed
4. Run the ETL pipeline as described in the README

### Sample Data Schema
```sql
CREATE TABLE sdud_analytics (
    state VARCHAR(2),
    year INT,
    quarter INT,
    year_quarter VARCHAR(10),
    utilization_type VARCHAR(50),
    product_name VARCHAR(255),
    product_name_norm VARCHAR(255),
    suppression_used VARCHAR(10),
    is_suppressed BIT,
    number_of_prescriptions BIGINT,
    total_amount_reimbursed DECIMAL(18,2),
    medicaid_amount_reimbursed DECIMAL(18,2),
    units_reimbursed BIGINT
);
```

### Alternative: Use Docker with SQL Server
The included `docker-compose.yml` sets up a SQL Server instance. You can:
1. Load your data directly into SQL Server
2. Skip the CSV step and use the dashboard directly

## Privacy & Compliance
This project respects CMS privacy guidelines:
- Suppressed records (per CMS rules) are tracked but excluded from analytics
- No PHI or PII is included in this repository
- All metrics aggregate across multiple records
