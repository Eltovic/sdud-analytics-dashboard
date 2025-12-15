# Career Materials — SDUD Project

## Resume Bullet Points

### Data Engineer / Analytics Engineer
**State Drug Utilization Dashboard | Python, SQL Server, Dash, Docker**
- Built end-to-end analytics platform processing 100K+ Medicaid drug utilization records; designed ETL pipeline with pandas/SQLAlchemy to clean, normalize, and load CSV data into SQL Server analytics schema
- Developed interactive Dash dashboard with advanced KPIs (suppression rate, Top 1% spend concentration, cost-per-Rx distribution) enabling state-level and national comparisons across 52 states and 2 utilization types
- Implemented exponential smoothing forecasting with 95% confidence intervals and scenario multipliers; added CSV/PNG export functionality using Plotly/Kaleido for policy reporting
- Containerized full stack with Docker (amd64 multi-platform build); created docker-compose orchestration with healthchecks, reducing deployment time from hours to minutes

### Business Intelligence Analyst
**Medicaid Drug Spend Analytics Platform | SQL, Python, Dash**
- Designed and delivered executive dashboard analyzing $XXM+ in Medicaid drug reimbursements; computed custom metrics including Top 1% spend share (Gini-style concentration) to identify cost drivers and inform policy decisions
- Automated quarterly KPI generation with Python scripts writing summary tables (state rankings, top drugs, cost distributions) to SQL; reduced manual reporting effort by 80%
- Created interactive forecasting module with confidence intervals, enabling "what-if" scenario planning with adjustable multipliers for budget projections
- Collaborated with stakeholders to normalize 50K+ product names and exclude suppressed records per CMS privacy guidelines, ensuring data quality and regulatory compliance

### Full-Stack Data Analyst
**Healthcare Analytics Dashboard | Python, SQL Server, Dash, Docker**
- Architected and deployed containerized analytics platform for Medicaid drug utilization data; integrated SQL Server backend with Plotly Dash frontend to deliver real-time KPIs and forecasting to non-technical users
- Performed exploratory data analysis on 100K+ pharmacy claims; identified suppression patterns, calculated therapeutic class proxies, and designed cost-per-prescription distribution charts for outlier detection
- Built time-series forecasting engine using statsmodels (ETS) with residual-based confidence intervals; validated model accuracy and provided scenario planning tools for policy analysts
- Documented complete project with README, Docker assets, and deployment guide; enabled reproducible dev environment setup and one-command stack deployment (`docker-compose up`)

---

## LinkedIn Post

🚀 **Excited to share my latest project: State Drug Utilization Dashboard (SDUD)** 🚀

Just wrapped up an end-to-end analytics platform that transforms Medicaid drug utilization data into actionable insights for healthcare policy decisions.

**What I built:**
📊 Interactive Dash dashboard with executive KPIs and forecasting
💊 Analytics on 100K+ pharmacy claims across 52 states
📈 Exponential smoothing forecasts with 95% confidence intervals
🐳 Fully containerized stack (Docker + docker-compose) for one-command deployment

**Technical highlights:**
• ETL pipeline: Python + pandas + SQLAlchemy → SQL Server
• Advanced metrics: Top 1% spend concentration (cost inequality), suppression rate tracking, therapeutic class analysis
• Export features: CSV/PNG downloads for reporting
• Scenario planning: "What-if" multipliers for budget forecasting

**Key outcomes:**
✅ Reduced manual reporting from hours to minutes with automated KPI generation
✅ Enabled data-driven policy discussions with interactive state/national comparisons
✅ Built production-ready deployment with healthchecks and environment-based configuration

This project showcases my skills in data engineering, analytics, visualization, and DevOps. From raw CSV to deployed dashboard, every line of code was an opportunity to solve real-world problems.

Check out the full repo and documentation (link in comments)! Happy to discuss the technical details or analytics approach.

#DataEngineering #Analytics #Python #SQL #Docker #Dash #Healthcare #DataVisualization #MachineLearning

---

## 2-Minute Interview Explanation

**"Can you walk me through a recent project you're proud of?"**

**[Project Overview — 15 seconds]**
"Sure! I built an analytics platform called the State Drug Utilization Dashboard that analyzes Medicaid pharmacy data. The goal was to help policymakers understand drug spending patterns and forecast future costs. I took this from raw CSV files all the way to a production-ready containerized dashboard."

**[Technical Approach — 45 seconds]**
"On the data engineering side, I designed an ETL pipeline using Python, pandas, and SQLAlchemy. The source data had over 100,000 records with inconsistencies—things like product names that needed normalization and suppressed records due to CMS privacy rules. I cleaned and transformed the data, then loaded it into SQL Server with proper indexes and analytics-ready schemas.

For the analytics layer, I computed custom KPIs that weren't in the raw data. One key metric I developed is the 'Top 1% Spend Share'—essentially a concentration index that shows what fraction of total spending is captured by the most expensive 1% of prescriptions. This helps identify cost drivers and outliers.

On the visualization side, I built an interactive dashboard using Plotly Dash. Users can filter by state, year, quarter, and toggle between state-only or state-versus-national comparisons. The forecasting tab uses exponential smoothing with confidence intervals, plus a scenario multiplier so analysts can model 'what-if' budget scenarios."

**[DevOps & Deployment — 30 seconds]**
"For deployment, I containerized everything with Docker, including a multi-platform build for ARM Macs. I created a docker-compose file that spins up both SQL Server and the dashboard with health checks and environment-based configuration. This reduced setup from hours of manual steps to literally one command: `docker-compose up`. I also added CSV and PNG export features so users can download reports for presentations."

**[Impact & Learnings — 30 seconds]**
"The impact was significant—automated reporting that used to take hours now runs in minutes, and the interactive forecasting gives policymakers a tool they didn't have before. On a personal level, this project deepened my skills in time-series modeling, Docker orchestration, and end-to-end system design. I also learned how to balance technical complexity with usability—making sure the dashboard is intuitive for non-technical stakeholders.

I documented everything thoroughly with a README, architecture diagrams, and run instructions, so the project is fully reproducible and ready for handoff or collaboration."

**[Closing — 10 seconds]**
"I'm really proud of how it came together—from data quality issues to deployment, it's a complete example of turning messy real-world data into actionable insights."

---

## Elevator Pitch (30 seconds)

"I recently built an end-to-end analytics platform for Medicaid drug data. It ingests and cleans 100K+ pharmacy claims, computes custom KPIs like spend concentration and suppression rates, and delivers an interactive Dash dashboard with forecasting and export features. The entire stack—SQL Server, Python, and the dashboard—is containerized with Docker for one-command deployment. It automates what used to be hours of manual work and gives policymakers a tool to model budget scenarios and identify cost drivers."

---

## Technical Deep-Dive Questions & Answers

### Q: "How did you handle data quality issues?"
**A:** "The raw data had several challenges. First, product names were inconsistent—same drug, different spellings. I implemented a normalization routine that strips special characters, standardizes casing, and groups by base name. Second, some records were flagged as suppressed per CMS privacy rules. I added a filter to exclude those from analytics while still tracking suppression rates as a KPI. Third, there were null values and zero prescriptions in some rows. I used `NULLIF` in SQL queries and pandas `.dropna()` to handle those edge cases without skewing aggregations."

### Q: "Why did you choose exponential smoothing for forecasting?"
**A:** "I chose exponential smoothing (ETS) because the time series data is quarterly with seasonal patterns—drug spending typically has quarterly cycles due to flu seasons, formulary changes, etc. ETS handles trend and seasonality well with relatively few data points (we had ~8-12 quarters per state). I also implemented a fallback 'naive' forecast (last value carried forward) in case the model fails to fit, which ensures the dashboard always returns a forecast. For confidence intervals, I used a residual-based approach: I calculated the standard error from fit residuals and expanded it with the square root of the forecast horizon."

### Q: "How did you optimize SQL queries for performance?"
**A:** "I added indexes on the most-queried columns: `state`, `year`, `quarter`, `utilization_type`, and `is_suppressed`. For aggregations, I used SQL's `GROUP BY` with `TOP N` to limit result sets. I also created 'gold' summary tables—pre-aggregated KPIs stored in SQL—so the dashboard doesn't have to recompute top drugs or state rankings on every load. For the dashboard queries, I used parameterized SQL via SQLAlchemy's `text()` to prevent injection and enable query plan caching."

### Q: "What challenges did you face with Docker?"
**A:** "The biggest challenge was building for Apple Silicon (ARM). The Microsoft ODBC driver for SQL Server is x86_64-only, so I had to use `docker buildx` with `--platform=linux/amd64` to ensure the container could install `msodbcsql18`. I also had to bind the Dash server to `0.0.0.0` instead of `127.0.0.1` so the container port could be accessed from the host. For orchestration, I added a docker-compose file with health checks and `depends_on` to ensure SQL Server is ready before the dashboard starts."

### Q: "How would you scale this for production?"
**A:** "For production, I'd add several layers:
1. **Data validation**: Implement schema checks and data quality tests (Great Expectations or custom SQL tests).
2. **Caching**: Add Redis or Dash's built-in memoization to cache query results and reduce DB load.
3. **Monitoring**: Integrate application performance monitoring (APM) like Datadog or New Relic; add logging with structured JSON logs.
4. **CI/CD**: Set up GitHub Actions to run tests, lint code, and build/push Docker images on merge.
5. **Database scaling**: Move to a managed SQL service (Azure SQL or RDS) with read replicas for query offloading.
6. **Authentication**: Add user auth with OAuth or SAML if the dashboard needs to be multi-tenant.
7. **Kubernetes**: Deploy to AKS/EKS with horizontal pod autoscaling and ingress for SSL termination."

---

## Key Talking Points for Behavioral Questions

### "Tell me about a time you solved a complex technical problem."
**Context:** Raw drug utilization data with inconsistent product names, suppressed rows, and no pre-computed KPIs.  
**Action:** Designed normalization logic, implemented suppression filters, and created custom metrics (Top 1% spend share).  
**Result:** Clean analytics-ready data; dashboard delivers insights that weren't available before.  
**Learning:** Importance of data quality upfront; how to balance automation with manual spot-checks.

### "Describe a time you worked with stakeholders."
**Context:** Policy analysts needed forecasting for budget planning but lacked technical background.  
**Action:** Built intuitive UI with dropdowns and scenario multipliers; added export features for reports; wrote user-friendly documentation.  
**Result:** Non-technical users can run forecasts and generate reports independently; reduced back-and-forth requests.  
**Learning:** Simplicity and clarity win over feature overload; always validate assumptions with end users.

### "How do you prioritize when working on multiple features?"
**Context:** Had to balance core analytics, forecasting, exports, and Docker deployment.  
**Action:** Built MVP (basic dashboard + KPIs) first, then added forecasting, then export, then containerization. Each phase was tested before moving to the next.  
**Result:** Delivered working product incrementally; each milestone was deployable.  
**Learning:** Iterative delivery reduces risk; small wins build momentum.

---

## Project Metrics & Impact (for interviews)

- **Data Volume:** 100,000+ pharmacy claim records
- **Coverage:** 52 states, 2 utilization types, multiple years/quarters
- **KPIs Delivered:** 6+ (total reimbursed, Medicaid share, prescriptions, units, cost-per-Rx, Top 1% spend share)
- **Forecasting:** Exponential smoothing with 95% CI, horizon up to 8 quarters
- **Automation:** Reduced manual reporting from ~4 hours to <5 minutes
- **Deployment:** One-command stack startup (`docker-compose up`)
- **Documentation:** Complete README, architecture diagrams, run instructions, career materials
- **Technologies:** Python, pandas, SQLAlchemy, SQL Server, Dash, Plotly, statsmodels, Docker, docker-compose

---

## Additional Resources for Interviews

### GitHub Repo Structure
```
SDUD/
├── app/
│   └── dashboard.py          # Main Dash application
├── scripts/
│   └── 04_phase3_eda_kpis.py # KPI generation & gold tables
├── Dockerfile                # Container definition
├── docker-compose.yml        # Full stack orchestration
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
└── CAREER_MATERIALS.md       # This file
```

### Live Demo Talking Points
- Show filters in action (state, year, quarter, utilization type, scope toggle)
- Highlight Top 1% spend share and explain the metric
- Demonstrate forecasting with confidence intervals and scenario multiplier
- Show CSV/PNG export dropdowns and explain use case
- Walk through docker-compose healthcheck and startup sequence

### Questions to Ask Interviewers
- "How does your team currently handle data quality and validation in analytics pipelines?"
- "What tools and frameworks do you use for containerization and deployment?"
- "How do you balance technical debt with new feature development in your analytics products?"
- "What's the typical workflow for deploying a new dashboard or analytics tool to stakeholders?"
