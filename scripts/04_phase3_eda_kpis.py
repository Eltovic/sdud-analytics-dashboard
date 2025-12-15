import pandas as pd
from sqlalchemy import create_engine

# --- connection ---
conn_str = (
    "mssql+pyodbc://sa:StrongPassword123!@localhost:1433/sdud"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&TrustServerCertificate=yes"
)
engine = create_engine(conn_str)

# --- load a light slice first (fast dev) ---
df = pd.read_sql("SELECT * FROM dbo.sdud_silver;", engine)

print("\n✅ Loaded from SQL:", df.shape)

# 1) Suppression rate
supp_rate = df["is_suppressed"].mean()
print(f"\n📌 Suppression rate: {supp_rate:.2%}")

# 2) Coverage of numeric fields (non-null)
num_cols = [
    "units_reimbursed",
    "number_of_prescriptions",
    "total_amount_reimbursed",
    "medicaid_amount_reimbursed",
    "non_medicaid_amount_reimbursed",
]
coverage = df[num_cols].notna().mean().sort_values(ascending=False)
print("\n📌 Numeric coverage (non-null proportion):")
print((coverage * 100).round(2).astype(str) + "%")

# 3) Top states by total reimbursed (excluding suppressed rows)
df_nonsupp = df[df["is_suppressed"] == False].copy()

# normalize product name for consistent grouping (operate on non-suppressed slice)
df_nonsupp["product_name_norm"] = (
    df_nonsupp["product_name"].str.upper().str.strip()
)

# exclude placeholder state code 'XX' for state-level KPIs
df_state = df_nonsupp[df_nonsupp["state"] != "XX"].copy()

top_states = (
    df_state.groupby("state", as_index=False)["total_amount_reimbursed"]
    .sum()
    .sort_values("total_amount_reimbursed", ascending=False)
    .head(10)
)
print("\n📌 Top 10 states by Total Amount Reimbursed (non-suppressed only):")
print(top_states)

# 4) High-cost drugs (top 10 by total reimbursed)
top_drugs = (
    df_state.groupby("product_name_norm", as_index=False)["total_amount_reimbursed"]
    .sum()
    .sort_values("total_amount_reimbursed", ascending=False)
    .head(10)
)
print("\n📌 Top 10 drugs by Total Amount Reimbursed (non-suppressed only):")
print(top_drugs)

# --- Persist summary tables back to SQL ---
# 1) State-level KPIs (full states summary)
state_kpis = (
    df_state.groupby("state", as_index=False)
    .agg(
        total_amount_reimbursed=("total_amount_reimbursed", "sum"),
        total_prescriptions=("number_of_prescriptions", "sum"),
        total_units_reimbursed=("units_reimbursed", "sum"),
        rows=("state", "count"),
    )
)

print("\n➡️ Writing `sdud_gold_state_kpis` to SQL (replace)...")
state_kpis.to_sql("sdud_gold_state_kpis", engine, if_exists="replace", index=False)

# 2) Top drugs (we'll persist the top-10 table as computed)
print("➡️ Writing `sdud_gold_top_drugs` to SQL (replace)...")
top_drugs.to_sql("sdud_gold_top_drugs", engine, if_exists="replace", index=False)

# 3) Cost per prescription distribution summary
# 5) Cost per prescription (guard against divide by zero)
df_nonsupp["cost_per_rx"] = (
    df_nonsupp["total_amount_reimbursed"] / df_nonsupp["number_of_prescriptions"]
)
cpp = df_nonsupp["cost_per_rx"].replace([pd.NA, pd.NaT, float("inf")], pd.NA).dropna()

# cost distribution summary
cpp_stats = cpp.describe(percentiles=[0.5, 0.9, 0.95, 0.99]).rename_axis("metric").reset_index()
cpp_stats.columns = ["metric", "value"]
print("➡️ Writing `sdud_gold_cost_distribution` to SQL (replace)...")
cpp_stats.to_sql("sdud_gold_cost_distribution", engine, if_exists="replace", index=False)

print("\n✅ Wrote summary tables: sdud_gold_state_kpis, sdud_gold_top_drugs, sdud_gold_cost_distribution")

# 5) Cost per prescription (guard against divide by zero)
df_nonsupp["cost_per_rx"] = (
    df_nonsupp["total_amount_reimbursed"] / df_nonsupp["number_of_prescriptions"]
)
cpp = df_nonsupp["cost_per_rx"].replace([pd.NA, pd.NaT, float("inf")], pd.NA).dropna()

print("\n📌 Cost per prescription summary (non-suppressed only):")
print(cpp.describe(percentiles=[0.5, 0.9, 0.95, 0.99]))