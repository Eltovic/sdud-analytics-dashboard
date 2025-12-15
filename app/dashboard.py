import io
import os
import datetime as dt

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.io as pio

# Optional forecasting dependency
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    HAS_STATSMODELS = True
except Exception:
    HAS_STATSMODELS = False

print(f"[dashboard] imports complete | statsmodels={HAS_STATSMODELS}")

# -----------------------------
# DB connection (env-configurable)
# -----------------------------
# If DATABASE_URL is provided, it takes precedence. Otherwise assemble from parts.
_DATABASE_URL = os.getenv("DATABASE_URL")
if _DATABASE_URL:
    engine = create_engine(_DATABASE_URL, pool_pre_ping=True)
else:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "1433"))
    DB_NAME = os.getenv("DB_NAME", "sdud")
    DB_USER = os.getenv("DB_USER", "sa")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "StrongPassword123!")
    ODBC_DRIVER = os.getenv("ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
    TRUST_CERT = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes")

    _url = URL.create(
        "mssql+pyodbc",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        query={
            "driver": ODBC_DRIVER,
            "TrustServerCertificate": TRUST_CERT,
        },
    )
    engine = create_engine(_url, pool_pre_ping=True)

# -----------------------------
# Helpers
# -----------------------------
def fetch_distinct(sql: str) -> list:
    with engine.begin() as conn:
        rows = conn.execute(text(sql)).fetchall()
    return [r[0] for r in rows if r[0] is not None]


def fmt_money0(x: float) -> str:
    return f"${x:,.0f}"


def fmt_num0(x: float) -> str:
    return f"{x:,.0f}"


def write_fig_png(fig):
    """
    Dash dcc.send_bytes expects a writer(buffer) callable.
    """
    def _writer(buffer: io.BytesIO):
        buffer.write(fig.to_image(format="png", scale=2))
    return _writer


# -----------------------------
# Load filter options
# -----------------------------
states = fetch_distinct(
    """
SELECT DISTINCT state
FROM dbo.sdud_analytics
WHERE state <> 'XX'
ORDER BY state
"""
)

years = fetch_distinct(
    """
SELECT DISTINCT [year]
FROM dbo.sdud_analytics
ORDER BY [year]
"""
)

quarters = fetch_distinct(
    """
SELECT DISTINCT quarter
FROM dbo.sdud_analytics
ORDER BY quarter
"""
)

util_types = fetch_distinct(
    """
SELECT DISTINCT utilization_type
FROM dbo.sdud_analytics
ORDER BY utilization_type
"""
)

DEFAULT_STATE = states[0] if states else None
DEFAULT_YEAR = int(max(years)) if years else None
DEFAULT_QUARTER = int(max(quarters)) if quarters else None
DEFAULT_UTIL = util_types[0] if util_types else None

print(f"[dashboard] options loaded | states={len(states)} years={len(years)} quarters={len(quarters)} util_types={len(util_types)}")

# -----------------------------
# Dash UI
# -----------------------------
app = Dash(__name__)
app.title = "SDUD Professional Dashboard"


def kpi_card(title: str, value_id: str):
    return html.Div(
        style={
            "border": "1px solid #ddd",
            "borderRadius": "14px",
            "padding": "14px",
            "minWidth": "180px",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.08)",
        },
        children=[
            html.Div(title, style={"fontSize": "12px", "opacity": 0.75}),
            html.Div(id=value_id, style={"fontSize": "22px", "fontWeight": "700", "marginTop": "6px"}),
        ],
    )


app.layout = html.Div(
    style={"fontFamily": "system-ui, -apple-system, Segoe UI, Roboto", "padding": "18px"},
    children=[
        html.H2("State Drug Utilization Data (SDUD) — Professional Dashboard", style={"marginBottom": "6px"}),
        html.Div("Source: dbo.sdud_analytics (non-suppressed rows only)", style={"opacity": 0.7, "marginBottom": "12px"}),

        # Filters row
        html.Div(
            style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "marginBottom": "10px"},
            children=[
                html.Div(
                    [
                        html.Div("State"),
                        dcc.Dropdown(
                            options=[{"label": s, "value": s} for s in states],
                            value=DEFAULT_STATE,
                            clearable=False,
                            id="state_dd",
                            style={"minWidth": "220px"},
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Div("Year"),
                        dcc.Dropdown(
                            options=[{"label": str(y), "value": int(y)} for y in years],
                            value=DEFAULT_YEAR,
                            clearable=False,
                            id="year_dd",
                            style={"minWidth": "160px"},
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Div("Quarter"),
                        dcc.Dropdown(
                            options=[{"label": f"Q{q}", "value": int(q)} for q in quarters],
                            value=DEFAULT_QUARTER,
                            clearable=False,
                            id="quarter_dd",
                            style={"minWidth": "160px"},
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Div("Utilization Type"),
                        dcc.Dropdown(
                            options=[{"label": u, "value": u} for u in util_types],
                            value=DEFAULT_UTIL,
                            clearable=False,
                            id="util_dd",
                            style={"minWidth": "200px"},
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Div("Scope"),
                        dcc.RadioItems(
                            options=[
                                {"label": "State only", "value": "state"},
                                {"label": "State vs National", "value": "state_vs_national"},
                            ],
                            value="state",
                            id="scope_toggle",
                            inline=True,
                            style={"marginTop": "6px"},
                        ),
                    ]
                ),
            ],
        ),

        # Professional download dropdown row
        html.Div(
            style={"display": "flex", "gap": "10px", "flexWrap": "wrap", "alignItems": "center", "marginBottom": "10px"},
            children=[
                dcc.Dropdown(
                    id="download_selector",
                    options=[
                        {"label": "KPIs (CSV)", "value": "kpi_csv"},
                        {"label": "Filtered Data (CSV) — top 5000 rows", "value": "data_csv"},
                        {"label": "Trend Chart (PNG)", "value": "trend_png"},
                        {"label": "Top Drivers Chart (PNG)", "value": "drivers_png"},
                        {"label": "Cost Distribution (PNG)", "value": "cost_png"},
                        {"label": "Forecast Chart (PNG)", "value": "forecast_png"},
                    ],
                    placeholder="Download…",
                    clearable=True,
                    style={"width": "360px"},
                ),
                html.Button("Download", id="download_btn", n_clicks=0),
                dcc.Download(id="download_target"),
            ],
        ),

        # KPI row
        html.Div(
            style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "marginBottom": "8px"},
            children=[
                kpi_card("Total Reimbursed", "kpi_total"),
                kpi_card("Medicaid Reimbursed", "kpi_medicaid"),
                kpi_card("Prescriptions", "kpi_rx"),
                kpi_card("Units", "kpi_units"),
                kpi_card("Cost per Rx", "kpi_cpp"),
                kpi_card("Top 1% Spend Share", "kpi_top1pc"),
            ],
        ),

        html.Div("Suppressed rows excluded per CMS privacy rules", style={"opacity": 0.65, "fontSize": "12px"}),

        dcc.Tabs(
            id="tabs",
            value="tab_exec",
            children=[
                dcc.Tab(
                    label="Executive Dashboard",
                    value="tab_exec",
                    children=[
                        html.Div(style={"height": "10px"}),
                        dcc.Graph(id="trend_graph"),
                        html.Div(
                            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "14px"},
                            children=[
                                dcc.Graph(id="top_drugs_graph"),
                                dcc.Graph(id="cpp_graph"),
                            ],
                        ),
                    ],
                ),
                dcc.Tab(
                    label="Forecasting",
                    value="tab_forecast",
                    children=[
                        html.Div(style={"height": "12px"}),
                        html.Div(
                            style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "alignItems": "center"},
                            children=[
                                html.Div(
                                    [
                                        html.Div("Forecast horizon (quarters)"),
                                        dcc.Dropdown(
                                            id="fc_horizon",
                                            options=[{"label": str(n), "value": n} for n in [4, 8, 12]],
                                            value=4,
                                            clearable=False,
                                            style={"minWidth": "220px"},
                                        ),
                                    ]
                                ),
                                html.Div(
                                    [
                                        html.Div("Scenario: spend multiplier"),
                                        dcc.Slider(
                                            id="fc_multiplier",
                                            min=0.80,
                                            max=1.30,
                                            step=0.01,
                                            value=1.00,
                                            marks={0.8: "0.80", 1.0: "1.00", 1.2: "1.20", 1.3: "1.30"},
                                        ),
                                        html.Div(id="fc_multiplier_label", style={"fontSize": "12px", "opacity": 0.75}),
                                    ],
                                    style={"minWidth": "420px"},
                                ),
                                html.Div(
                                    [
                                        html.Div("Model"),
                                        dcc.Dropdown(
                                            id="fc_model",
                                            options=[
                                                {"label": "ETS (Holt-Winters)", "value": "ets"},
                                                {"label": "Naive (last value)", "value": "naive"},
                                            ],
                                            value="ets" if HAS_STATSMODELS else "naive",
                                            clearable=False,
                                            style={"minWidth": "220px"},
                                        ),
                                    ]
                                ),
                            ],
                        ),
                        html.Div(style={"height": "10px"}),
                        dcc.Graph(id="forecast_graph"),
                        html.Div(id="forecast_table"),
                        html.Div(
                            id="forecast_note",
                            style={"marginTop": "8px", "fontSize": "12px", "opacity": 0.75},
                        ),
                    ],
                ),
            ],
        ),

        # Stores for downloads
        dcc.Store(id="store_kpis"),
        dcc.Store(id="store_filtered_head"),
        dcc.Store(id="store_fig_trend"),
        dcc.Store(id="store_fig_top"),
        dcc.Store(id="store_fig_cpp"),
        dcc.Store(id="store_fig_fc"),
    ],
)


# -----------------------------
# Executive callback (KPIs + charts)
# -----------------------------
@app.callback(
    Output("kpi_total", "children"),
    Output("kpi_medicaid", "children"),
    Output("kpi_rx", "children"),
    Output("kpi_units", "children"),
    Output("kpi_cpp", "children"),
    Output("kpi_top1pc", "children"),
    Output("trend_graph", "figure"),
    Output("top_drugs_graph", "figure"),
    Output("cpp_graph", "figure"),
    Output("store_kpis", "data"),
    Output("store_filtered_head", "data"),
    Output("store_fig_trend", "data"),
    Output("store_fig_top", "data"),
    Output("store_fig_cpp", "data"),
    Input("state_dd", "value"),
    Input("year_dd", "value"),
    Input("quarter_dd", "value"),
    Input("util_dd", "value"),
    Input("scope_toggle", "value"),
)
def update_executive(state, year, quarter, util_type, scope):
    empty = px.bar(title="No data")
    if not (state and year and quarter and util_type and scope):
        return "—", "—", "—", "—", "—", "—", empty, empty, empty, {}, [], {}, {}, {}

    params_state = {"state": state, "year": int(year), "quarter": int(quarter), "util": util_type}
    params_nat = {"year": int(year), "quarter": int(quarter), "util": util_type}

    # KPI
    kpi_state_sql = """
SELECT
  SUM(total_amount_reimbursed) AS total_reimbursed,
  SUM(medicaid_amount_reimbursed) AS medicaid_reimbursed,
  SUM(number_of_prescriptions) AS prescriptions,
  SUM(units_reimbursed) AS units
FROM dbo.sdud_analytics
WHERE state = :state AND [year] = :year AND quarter = :quarter AND utilization_type = :util;
"""
    kpi_nat_sql = """
SELECT
  SUM(total_amount_reimbursed) AS total_reimbursed,
  SUM(medicaid_amount_reimbursed) AS medicaid_reimbursed,
  SUM(number_of_prescriptions) AS prescriptions,
  SUM(units_reimbursed) AS units
FROM dbo.sdud_analytics
WHERE state <> 'XX' AND [year] = :year AND quarter = :quarter AND utilization_type = :util;
"""

    with engine.begin() as conn:
        k = conn.execute(text(kpi_state_sql), params_state).mappings().first()

    total = float(k["total_reimbursed"] or 0.0)
    medicaid = float(k["medicaid_reimbursed"] or 0.0)
    rx = float(k["prescriptions"] or 0.0)
    units = float(k["units"] or 0.0)
    cpp = (total / rx) if rx > 0 else 0.0

    kpi_total_txt = fmt_money0(total)
    kpi_medicaid_txt = fmt_money0(medicaid)
    kpi_rx_txt = fmt_num0(rx)
    kpi_units_txt = fmt_num0(units)

    kpi_cpp_txt = f"${cpp:,.2f}"
    if scope == "state_vs_national":
        with engine.begin() as conn:
            kn = conn.execute(text(kpi_nat_sql), params_nat).mappings().first()
        nat_total = float(kn["total_reimbursed"] or 0.0)
        nat_rx = float(kn["prescriptions"] or 0.0)
        nat_cpp = (nat_total / nat_rx) if nat_rx > 0 else 0.0
        kpi_cpp_txt = f"${cpp:,.2f} (Nat ${nat_cpp:,.2f})"

    # Trend
    trend_state_sql = """
SELECT year_quarter, quarter, SUM(total_amount_reimbursed) AS total_reimbursed
FROM dbo.sdud_analytics
WHERE state = :state AND [year] = :year AND utilization_type = :util
GROUP BY year_quarter, quarter
ORDER BY quarter;
"""
    trend_nat_sql = """
SELECT year_quarter, quarter, SUM(total_amount_reimbursed) AS total_reimbursed
FROM dbo.sdud_analytics
WHERE state <> 'XX' AND [year] = :year AND utilization_type = :util
GROUP BY year_quarter, quarter
ORDER BY quarter;
"""
    trend_state = pd.read_sql(text(trend_state_sql), engine, params={"state": state, "year": int(year), "util": util_type})
    trend_state["scope"] = "State"

    if scope == "state_vs_national":
        trend_nat = pd.read_sql(text(trend_nat_sql), engine, params={"year": int(year), "util": util_type})
        trend_nat["scope"] = "National"
        trend_df = pd.concat([trend_state, trend_nat], ignore_index=True)
        trend_fig = px.line(
            trend_df,
            x="year_quarter",
            y="total_reimbursed",
            color="scope",
            title=f"Total Reimbursed Trend — {state} ({year}) [{util_type}]",
            markers=True,
        )
    else:
        trend_fig = px.line(
            trend_state,
            x="year_quarter",
            y="total_reimbursed",
            title=f"Total Reimbursed Trend — {state} ({year}) [{util_type}]",
            markers=True,
        )
    trend_fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    trend_fig.update_yaxes(tickformat="$,")

    # Top drivers (first token proxy)
    top_state_sql = """
SELECT TOP 15
  LEFT(product_name_norm, CHARINDEX(' ', product_name_norm + ' ') - 1) AS thera_class,
  SUM(total_amount_reimbursed) AS total_reimbursed
FROM dbo.sdud_analytics
WHERE state = :state AND [year] = :year AND quarter = :quarter AND utilization_type = :util
GROUP BY LEFT(product_name_norm, CHARINDEX(' ', product_name_norm + ' ') - 1)
ORDER BY total_reimbursed DESC;
"""
    top_nat_sql = """
SELECT TOP 15
  LEFT(product_name_norm, CHARINDEX(' ', product_name_norm + ' ') - 1) AS thera_class,
  SUM(total_amount_reimbursed) AS total_reimbursed
FROM dbo.sdud_analytics
WHERE state <> 'XX' AND [year] = :year AND quarter = :quarter AND utilization_type = :util
GROUP BY LEFT(product_name_norm, CHARINDEX(' ', product_name_norm + ' ') - 1)
ORDER BY total_reimbursed DESC;
"""
    top_state = pd.read_sql(text(top_state_sql), engine, params=params_state)
    top_state["scope"] = "State"

    if scope == "state_vs_national":
        top_nat = pd.read_sql(text(top_nat_sql), engine, params=params_nat)
        top_nat["scope"] = "National"
        top_df = pd.concat([top_state, top_nat], ignore_index=True)
        order = (
            top_df.groupby("thera_class")["total_reimbursed"]
            .sum()
            .sort_values(ascending=False)
            .index.tolist()
        )
        top_fig = px.bar(
            top_df,
            x="total_reimbursed",
            y="thera_class",
            color="scope",
            orientation="h",
            title=f"Top cost drivers by condition — {state} {year}Q{quarter}",
            category_orders={"thera_class": order},
        )
        top_fig.update_layout(barmode="group")
    else:
        top_df = top_state.sort_values("total_reimbursed", ascending=True)
        top_fig = px.bar(
            top_df,
            x="total_reimbursed",
            y="thera_class",
            orientation="h",
            title=f"Top cost drivers by condition — {state} {year}Q{quarter}",
        )
    top_fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), yaxis_title="")
    top_fig.update_xaxes(tickformat="$,")

    # Cost per Rx distribution + top 1% spend share
    cpp_state_sql = """
SELECT
  (total_amount_reimbursed / NULLIF(number_of_prescriptions, 0)) AS cost_per_rx,
  number_of_prescriptions,
  total_amount_reimbursed
FROM dbo.sdud_analytics
WHERE state = :state AND [year] = :year AND quarter = :quarter AND utilization_type = :util
  AND number_of_prescriptions > 0 AND total_amount_reimbursed IS NOT NULL;
"""
    cpp_nat_sql = """
SELECT
  (total_amount_reimbursed / NULLIF(number_of_prescriptions, 0)) AS cost_per_rx,
  number_of_prescriptions,
  total_amount_reimbursed
FROM dbo.sdud_analytics
WHERE state <> 'XX' AND [year] = :year AND quarter = :quarter AND utilization_type = :util
  AND number_of_prescriptions > 0 AND total_amount_reimbursed IS NOT NULL;
"""

    def top1_spend_share(df_in: pd.DataFrame) -> float:
        if df_in is None or df_in.empty:
            return 0.0
        dfc = df_in.dropna().copy()
        dfc = dfc[dfc["number_of_prescriptions"] > 0]
        if dfc.empty:
            return 0.0

        dfc = dfc.sort_values("cost_per_rx", ascending=False)
        total_rx = float(dfc["number_of_prescriptions"].sum())
        total_spend = float(dfc["total_amount_reimbursed"].sum())
        if total_rx <= 0 or total_spend <= 0:
            return 0.0

        threshold = total_rx * 0.01
        cum_rx = 0.0
        top_spend = 0.0

        for _, r in dfc.iterrows():
            rx_i = float(r["number_of_prescriptions"])
            cpp_i = float(r["cost_per_rx"])
            if rx_i <= 0:
                continue
            if cum_rx + rx_i <= threshold:
                top_spend += cpp_i * rx_i
                cum_rx += rx_i
            else:
                remaining = threshold - cum_rx
                if remaining > 0:
                    top_spend += cpp_i * remaining
                break

        return top_spend / total_spend

    cpp_state = pd.read_sql(text(cpp_state_sql), engine, params=params_state).dropna()
    cpp_state["scope"] = "State"
    state_share = top1_spend_share(cpp_state)
    kpi_top1_txt = f"{state_share:.2%}" if state_share > 0 else "—"

    if scope == "state_vs_national":
        cpp_nat = pd.read_sql(text(cpp_nat_sql), engine, params=params_nat).dropna()
        cpp_nat["scope"] = "National"
        nat_share = top1_spend_share(cpp_nat)
        kpi_top1_txt = f"{state_share:.2%} (Nat {nat_share:.2%})"
        cpp_df = pd.concat([cpp_state, cpp_nat], ignore_index=True)
    else:
        cpp_df = cpp_state

    if len(cpp_df) > 250000:
        cpp_df = cpp_df.sample(250000, random_state=42)

    if scope == "state_vs_national":
        cpp_fig = px.histogram(
            cpp_df,
            x="cost_per_rx",
            color="scope",
            nbins=60,
            title=f"Cost per Prescription Distribution — {state} {year}Q{quarter}",
            opacity=0.6,
        )
        cpp_fig.update_layout(barmode="overlay")
    else:
        cpp_fig = px.histogram(
            cpp_df,
            x="cost_per_rx",
            nbins=60,
            title=f"Cost per Prescription Distribution — {state} {year}Q{quarter}",
        )

    cpp_fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    if len(cpp_df):
        cpp_fig.update_xaxes(range=[0, float(cpp_df["cost_per_rx"].quantile(0.99))], tickformat="$,")
    else:
        cpp_fig.update_xaxes(range=[0, 1], tickformat="$,")

    # Filtered data sample (TOP 5000)
    filtered_head_sql = """
SELECT TOP 5000 *
FROM dbo.sdud_analytics
WHERE state = :state AND [year] = :year AND quarter = :quarter AND utilization_type = :util;
"""
    head_df = pd.read_sql(text(filtered_head_sql), engine, params=params_state)

    kpis_payload = {
        "state": state,
        "year": int(year),
        "quarter": int(quarter),
        "utilization_type": util_type,
        "total_reimbursed": total,
        "medicaid_reimbursed": medicaid,
        "prescriptions": rx,
        "units": units,
        "cost_per_rx": cpp,
        "top1_spend_share": state_share,
        "as_of": dt.datetime.now().isoformat(timespec="seconds"),
    }

    return (
        kpi_total_txt,
        kpi_medicaid_txt,
        kpi_rx_txt,
        kpi_units_txt,
        kpi_cpp_txt,
        kpi_top1_txt,
        trend_fig,
        top_fig,
        cpp_fig,
        kpis_payload,
        head_df.to_dict("records"),
        trend_fig.to_dict(),
        top_fig.to_dict(),
        cpp_fig.to_dict(),
    )


# -----------------------------
# Forecast tab callback
# -----------------------------
@app.callback(
    Output("forecast_graph", "figure"),
    Output("forecast_table", "children"),
    Output("forecast_note", "children"),
    Output("fc_multiplier_label", "children"),
    Output("store_fig_fc", "data"),
    Input("state_dd", "value"),
    Input("util_dd", "value"),
    Input("scope_toggle", "value"),
    Input("fc_horizon", "value"),
    Input("fc_multiplier", "value"),
    Input("fc_model", "value"),
)
def update_forecast(state, util_type, scope, horizon, multiplier, model_name):
    empty = px.line(title="No forecast data")
    if not (state and util_type and horizon and multiplier and model_name and scope):
        return empty, "—", "", "", {}

    scope_note = "Forecast uses State series."

    ts_sql = """
SELECT
  [year],
  quarter,
  MIN(year_quarter) AS year_quarter,
  SUM(total_amount_reimbursed) AS total_reimbursed
FROM dbo.sdud_analytics
WHERE state = :state AND utilization_type = :util
GROUP BY [year], quarter
ORDER BY [year], quarter;
"""
    ts = pd.read_sql(text(ts_sql), engine, params={"state": state, "util": util_type})
    if ts.empty or ts["total_reimbursed"].isna().all():
        return empty, "No time series available for forecast.", scope_note, f"Multiplier: {multiplier:.2f}", {}

    ts = ts.copy()
    ts["total_reimbursed"] = ts["total_reimbursed"].astype(float)

    # Create quarterly timestamps
    ts["date"] = pd.PeriodIndex(
        ts["year"].astype(int).astype(str) + "Q" + ts["quarter"].astype(int).astype(str),
        freq="Q",
    ).to_timestamp()
    ts = ts.sort_values("date")

    fc_method_used = model_name
    fc_values = None
    fc_lower = None
    fc_upper = None

    if model_name == "ets" and HAS_STATSMODELS and len(ts) >= 8:
        try:
            fit = ExponentialSmoothing(
                ts["total_reimbursed"],
                trend="add",
                seasonal="add",
                seasonal_periods=4,
                initialization_method="estimated",
            ).fit(optimized=True)
            fc_obj = fit.forecast(int(horizon))
            fc_values = fc_obj if isinstance(fc_obj, np.ndarray) else fc_obj.values
            
            # Compute 95% CI using residual-based approach
            residuals = fit.fittedvalues - ts["total_reimbursed"]
            std_error = np.std(residuals)
            z_score = 1.96  # 95% CI
            fc_lower = []
            fc_upper = []
            for h_i in range(1, int(horizon) + 1):
                expansion = np.sqrt(h_i)  # Error grows with horizon
                se = std_error * expansion
                fc_lower.append(fc_values[h_i - 1] - z_score * se)
                fc_upper.append(fc_values[h_i - 1] + z_score * se)
            fc_lower = np.array(fc_lower)
            fc_upper = np.array(fc_upper)
        except Exception:
            fc_values = None
            fc_method_used = "naive"

    if fc_values is None:
        last = float(ts["total_reimbursed"].iloc[-1])
        fc_values = [last] * int(horizon)
        fc_method_used = "naive"
        # Simple CI for naive: use historical std
        hist_std = ts["total_reimbursed"].std()
        z_score = 1.96
        fc_lower = np.array([last - z_score * hist_std * np.sqrt(i) for i in range(1, int(horizon) + 1)])
        fc_upper = np.array([last + z_score * hist_std * np.sqrt(i) for i in range(1, int(horizon) + 1)])

    fc_values = pd.Series(fc_values) * float(multiplier)
    if fc_lower is not None:
        fc_lower = pd.Series(fc_lower) * float(multiplier)
        fc_upper = pd.Series(fc_upper) * float(multiplier)

    last_period = pd.Period(ts["date"].iloc[-1], freq="Q")
    fc_periods = [last_period + i for i in range(1, int(horizon) + 1)]
    fc_dates = [p.to_timestamp() for p in fc_periods]
    fc_labels = [str(p) for p in fc_periods]

    fc_df = pd.DataFrame(
        {
            "date": fc_dates,
            "period": fc_labels,
            "forecast_total_reimbursed": fc_values.values,
            "lower_bound": fc_lower.values if fc_lower is not None else fc_values.values,
            "upper_bound": fc_upper.values if fc_upper is not None else fc_values.values,
        }
    )

    hist_df = ts[["date", "total_reimbursed"]].copy()
    hist_df["series"] = "Historical"
    fplot = fc_df.rename(columns={"forecast_total_reimbursed": "total_reimbursed"}).copy()
    fplot["series"] = f"Forecast ({fc_method_used.upper()})"

    plot_df = pd.concat([hist_df, fplot[["date", "total_reimbursed", "series"]]], ignore_index=True)

    fig = px.line(
        plot_df,
        x="date",
        y="total_reimbursed",
        color="series",
        markers=True,
        title=f"Forecast: Total Amount Reimbursed — {state} [{util_type}] (95% CI)",
    )
    
    # Add confidence interval shaded bands
    if fc_lower is not None and fc_upper is not None:
        fig.add_scatter(
            x=fc_dates,
            y=fc_upper.values,
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
        fig.add_scatter(
            x=fc_dates,
            y=fc_lower.values,
            mode="lines",
            line=dict(width=0),
            fillcolor="rgba(68, 68, 68, 0.2)",
            fill="tonexty",
            name="95% CI",
            hovertemplate="<b>95% CI</b><br>Date: %{x}<br>Lower: $%{y:,.0f}<extra></extra>",
        )
    
    fig.update_yaxes(tickformat="$,")
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))

    # Table with CI bounds
    tbl = fc_df.copy()
    tbl["forecast_total_reimbursed"] = tbl["forecast_total_reimbursed"].map(lambda v: f"${v:,.0f}")
    tbl["lower_bound"] = tbl["lower_bound"].map(lambda v: f"${v:,.0f}")
    tbl["upper_bound"] = tbl["upper_bound"].map(lambda v: f"${v:,.0f}")

    table = html.Table(
        style={"borderCollapse": "collapse", "width": "100%", "maxWidth": "820px"},
        children=[
            html.Thead(
                html.Tr(
                    [
                        html.Th("Quarter", style={"textAlign": "left", "borderBottom": "1px solid #ddd", "padding": "8px"}),
                        html.Th("Forecast", style={"textAlign": "right", "borderBottom": "1px solid #ddd", "padding": "8px"}),
                        html.Th("Lower (95%)", style={"textAlign": "right", "borderBottom": "1px solid #ddd", "padding": "8px"}),
                        html.Th("Upper (95%)", style={"textAlign": "right", "borderBottom": "1px solid #ddd", "padding": "8px"}),
                    ]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(r["period"], style={"padding": "8px", "borderBottom": "1px solid #f0f0f0"}),
                            html.Td(r["forecast_total_reimbursed"], style={"padding": "8px", "textAlign": "right", "borderBottom": "1px solid #f0f0f0"}),
                            html.Td(r["lower_bound"], style={"padding": "8px", "textAlign": "right", "borderBottom": "1px solid #f0f0f0", "color": "#666"}),
                            html.Td(r["upper_bound"], style={"padding": "8px", "textAlign": "right", "borderBottom": "1px solid #f0f0f0", "color": "#666"}),
                        ]
                    )
                    for _, r in tbl.iterrows()
                ]
            ),
        ],
    )

    note = (
        f"Model: {fc_method_used.upper()} | Horizon: {horizon} quarters | "
        f"Scenario multiplier: {multiplier:.2f} | {scope_note}"
    )

    return fig, table, note, f"Multiplier: {multiplier:.2f}", fig.to_dict()


# -----------------------------
# Download callback (dropdown + Download button)
# -----------------------------
@app.callback(
    Output("download_target", "data"),
    Input("download_btn", "n_clicks"),
    State("download_selector", "value"),
    State("store_kpis", "data"),
    State("store_filtered_head", "data"),
    State("store_fig_trend", "data"),
    State("store_fig_top", "data"),
    State("store_fig_cpp", "data"),
    State("store_fig_fc", "data"),
    prevent_initial_call=True,
)
def handle_download(n_clicks, selection, kpis, head_rows, fig_trend, fig_top, fig_cpp, fig_fc):
    if not selection:
        raise PreventUpdate

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    # CSV downloads
    if selection == "kpi_csv":
        df = pd.DataFrame([kpis or {}])
        return dcc.send_data_frame(df.to_csv, f"sdud_kpis_{ts}.csv", index=False)

    if selection == "data_csv":
        df = pd.DataFrame(head_rows or [])
        return dcc.send_data_frame(df.to_csv, f"sdud_filtered_top5000_{ts}.csv", index=False)

    # PNG downloads
    if selection == "trend_png":
        fig = pio.from_json(pio.to_json(fig_trend)) if fig_trend else px.line(title="No trend chart")
        return dcc.send_bytes(write_fig_png(fig), f"sdud_trend_{ts}.png")

    if selection == "drivers_png":
        fig = pio.from_json(pio.to_json(fig_top)) if fig_top else px.bar(title="No top drivers chart")
        return dcc.send_bytes(write_fig_png(fig), f"sdud_top_drivers_{ts}.png")

    if selection == "cost_png":
        fig = pio.from_json(pio.to_json(fig_cpp)) if fig_cpp else px.histogram(title="No cost distribution chart")
        return dcc.send_bytes(write_fig_png(fig), f"sdud_cost_distribution_{ts}.png")

    if selection == "forecast_png":
        fig = pio.from_json(pio.to_json(fig_fc)) if fig_fc else px.line(title="No forecast chart")
        return dcc.send_bytes(write_fig_png(fig), f"sdud_forecast_{ts}.png")

    raise PreventUpdate


if __name__ == "__main__":
    print("Starting Dash app on http://0.0.0.0:8050")
    app.run(host="0.0.0.0", port=8050, debug=True, use_reloader=False)