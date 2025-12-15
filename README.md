# SDUD — State Drug Utilization Dashboard

Project repository for a SQL-backed analytics platform and Dash dashboard that summarizes state-level drug utilization (Medicaid) data, computes key KPIs, and provides forecasting and exportable reporting.

**Architecture**

- CSV source data -> ingestion/cleaning scripts -> SQL Server (silver/analytics tables)
- Aggregation & KPI scripts -> gold summary tables (e.g., `sdud_gold_state_kpis`)
- Dash app (`app/dashboard.py`) reads from `dbo.sdud_analytics` / gold tables and renders interactive charts + exports

Simple flow:

CSV -> ETL scripts (scripts/) -> SQL Server
        |
        v
    Analytics schema (dbo.sdud_analytics)
        |
        v
    Dash UI (app/dashboard.py)

**Key metrics**
- Suppression rate: fraction of rows flagged/suppressed per CMS privacy rules (these rows are excluded from analytics)
- Top 1% Spend Share: fraction of total spend captured by the top 1% of prescriptions by cost-per-prescription (measures cost concentration)

**What's in this repo**
- `scripts/04_phase3_eda_kpis.py` — EDA and KPI generation; writes gold tables to SQL (`sdud_gold_state_kpis`, `sdud_gold_top_drugs`, `sdud_gold_cost_distribution`)
- `app/dashboard.py` — Dash app with executive dashboard, forecasting tab, and CSV/PNG export features
- `requirements.txt` — Python dependencies for local setup
- `Dockerfile` — Docker image for containerized deployment
- `docker-compose.yml` — Full stack (SQL Server + Dashboard) orchestration

Screenshots
- (Place screenshots in `docs/` and reference here.)

## How to run locally

1. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure database connection via environment variables (or `DATABASE_URL`). Defaults assume local SQL Server:
   - `DATABASE_URL` (optional, overrides all below). Example:
     `mssql+pyodbc://sa:StrongPassword123!@localhost:1433/sdud?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes`
   - `DB_HOST` (default: `localhost`)
   - `DB_PORT` (default: `1433`)
   - `DB_NAME` (default: `sdud`)
   - `DB_USER` (default: `sa`)
   - `DB_PASSWORD` (default: `StrongPassword123!`)
   - `ODBC_DRIVER` (default: `ODBC Driver 18 for SQL Server`)
   - `DB_TRUST_SERVER_CERTIFICATE` (default: `yes`)

3. Run the EDA / KPI script to generate gold tables (optional — the dashboard reads from `dbo.sdud_analytics`):

```bash
python scripts/04_phase3_eda_kpis.py
```

4. Start the Dash app

```bash
python app/dashboard.py
# then open http://127.0.0.1:8050
```

## Docker

### Using Docker Compose (Recommended)

The easiest way to run the entire stack (SQL Server + Dashboard) is with Docker Compose:

```bash
docker-compose up -d
```

This will:
- Start SQL Server on port 1433 with healthcheck
- Start the dashboard on port 8050 once SQL Server is ready
- Create a shared network for the services

Access the dashboard at `http://localhost:8050`.

To stop:

```bash
docker-compose down
```

To stop and remove volumes:

```bash
docker-compose down -v
```

### Manual Docker Build & Run

Build the Docker image (Apple Silicon / ARM Macs need amd64):

```bash
docker buildx build --platform=linux/amd64 -t sdud-dashboard . --load
```

Run the container (connecting to SQL Server on host):

```bash
docker run --platform=linux/amd64 --rm -p 8050:8050 \
  -e DB_HOST=host.docker.internal \
  -e DB_PORT=1433 \
  -e DB_NAME=master \
  -e DB_USER=sa \
  -e DB_PASSWORD=StrongPassword123! \
  sdud-dashboard
```

Or use a full connection string:

```bash
docker run --platform=linux/amd64 --rm -p 8050:8050 \
  -e DATABASE_URL="mssql+pyodbc://sa:StrongPassword123!@host.docker.internal:1433/master?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes" \
  sdud-dashboard
```

Access the dashboard at `http://localhost:8050`.

## Notes & Next steps
- Forecasting extension: add confidence intervals or bootstrap bands for policy-grade forecasts.
- Add automated smoke tests and a small README screenshot gallery in `docs/`.
- Healthcheck and monitoring for production deployments.
