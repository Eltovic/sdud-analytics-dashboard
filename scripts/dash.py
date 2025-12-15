import pandas as pd
from sqlalchemy import create_engine, text

from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# -----------------------------
# DB connection
# -----------------------------
CONN_STR = (
    "mssql+pyodbc://sa:StrongPassword123!@localhost:1433/sdud"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&TrustServerCertificate=yes"
)
engine = create_engine(CONN_STR)

# -----------------------------
# Helper: fetch filter options
# -----------------------------
def fetch_distinct(sql: str) -> list:
    with engine.begin() as conn:
        rows = conn.execute(text(sql)).fetchall()
    return [r[0] for r in rows if r[0] is not None]


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

# -----------------------------
# Dash UI
# -----------------------------
app = Dash(__name__)
app.title = "SDUD Executive Dashboard"


def kpi_card(title, value_id):
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
            html.Div(
                id=value_id,
                style={"fontSize": "22px", "fontWeight": "700", "marginTop": "6px"},
            ),
        ],
    )


app.layout = html.Div(
    style={"fontFamily": "system-ui, -apple-system, Segoe UI, Roboto", "padding": "18px"},
    children=[
        html.H2("State Drug Utilization Data (SDUD) — Executive Dashboard", style={"marginBottom": "6px"}),
        html.Div(
            "Source: dbo.sdud_analytics (non-suppressed rows only)",
            style={"opacity": 0.7, "marginBottom": "16px"},
        ),
        # Filters
        html.Div(
            style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "marginBottom": "14px"},
            children=[
                html.Div(
                    [
                        html.Div("State"),
                        dcc.Dropdown(
                            options=[{"label": s, "value": s} for s in states],
                            value=states[0] if states else None,
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
                            value=int(max(years)) if years else None,
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
                            value=int(max(quarters)) if quarters else None,
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
                            value=util_types[0] if util_types else None,
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
        # KPI row
        html.Div(
            style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "marginBottom": "10px"},
            children=[
                kpi_card("Total Reimbursed", "kpi_total"),
                kpi_card("Medicaid Reimbursed", "kpi_medicaid"),
                kpi_card("Prescriptions", "kpi_rx"),
                kpi_card("Units", "kpi_units"),
                kpi_card("Cost per Rx", "kpi_cpp"),
                kpi_card("Top 1% Spend Share", "kpi_top1pc"),
            ],
        ),
        html.Div(
            "Suppressed rows excluded per CMS privacy rules",
            style={"opacity": 0.65, "fontSize": "12px", "marginBottom": "14px"},
        ),
        # Charts
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr", "gap": "14px"},
            children=[
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
    ],
)

# -----------------------------
# Callbacks (SQL-driven)
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
    Input("state_dd", "value"),
    Input("year_dd", "value"),
    Input("quarter_dd", "value"),
    Input("util_dd", "value"),
    Input("scope_toggle", "value"),
)
def update_dashboard(state, year, quarter, util_type, scope):
    empty = px.bar(title="No data")

    # Need 6 outputs + 3 figures
    if not (state and year and quarter and util_type and scope):
        return "—", "—", "—", "—", "—", "—", empty, empty, empty

    fmt_money = lambda x: f"${x:,.0f}"
    fmt_num = lambda x: f"{x:,.0f}"

    params_state = {
        "state": state,
        "year": int(year),
        "quarter": int(quarter),
        "util": util_type,
    }
    params_nat = {"year": int(year), "quarter": int(quarter), "util": util_type}

    # -----------------------------
    # KPI (state + optional national CPP)
    # -----------------------------
    kpi_state_sql = """
    SELECT
      SUM(total_amount_reimbursed) AS total_reimbursed,
      SUM(medicaid_amount_reimbursed) AS medicaid_reimbursed,
      SUM(number_of_prescriptions) AS prescriptions,
      SUM(units_reimbursed) AS units
    FROM dbo.sdud_analytics
    WHERE state = :state
      AND [year] = :year
      AND quarter = :quarter
      AND utilization_type = :util;
    """

    kpi_nat_sql = """
    SELECT
      SUM(total_amount_reimbursed) AS total_reimbursed,
      SUM(medicaid_amount_reimbursed) AS medicaid_reimbursed,
      SUM(number_of_prescriptions) AS prescriptions,
      SUM(units_reimbursed) AS units
    FROM dbo.sdud_analytics
    WHERE state <> 'XX'
      AND [year] = :year
      AND quarter = :quarter
      AND utilization_type = :util;
    """

    with engine.begin() as conn:
        kpi_state = conn.execute(text(kpi_state_sql), params_state).mappings().first()

    total = float(kpi_state["total_reimbursed"] or 0.0)
    medicaid = float(kpi_state["medicaid_reimbursed"] or 0.0)
    rx = float(kpi_state["prescriptions"] or 0.0)
    units = float(kpi_state["units"] or 0.0)
    cpp = (total / rx) if rx > 0 else 0.0

    kpi_total_txt = fmt_money(total)
    kpi_medicaid_txt = fmt_money(medicaid)
    kpi_rx_txt = fmt_num(rx)
    kpi_units_txt = fmt_num(units)

    # default (state)
    kpi_cpp_txt = f"${cpp:,.2f}"

    # State vs national: show national CPP comparison
    if scope == "state_vs_national":
        with engine.begin() as conn:
            kpi_nat = conn.execute(text(kpi_nat_sql), params_nat).mappings().first()
        nat_total = float(kpi_nat["total_reimbursed"] or 0.0)
        nat_rx = float(kpi_nat["prescriptions"] or 0.0)
        nat_cpp = (nat_total / nat_rx) if nat_rx > 0 else 0.0
        kpi_cpp_txt = f"${cpp:,.2f} (Nat ${nat_cpp:,.2f})"

    # -----------------------------
    # Trend (all quarters for selected year)
    # -----------------------------
    trend_state_sql = """
    SELECT
      year_quarter,
      quarter,
      SUM(total_amount_reimbursed) AS total_reimbursed
    FROM dbo.sdud_analytics
    WHERE state = :state
      AND [year] = :year
      AND utilization_type = :util
    GROUP BY year_quarter, quarter
    ORDER BY quarter;
    """

    trend_nat_sql = """
    SELECT
      year_quarter,
      quarter,
      SUM(total_amount_reimbursed) AS total_reimbursed
    FROM dbo.sdud_analytics
    WHERE state <> 'XX'
      AND [year] = :year
      AND utilization_type = :util
    GROUP BY year_quarter, quarter
    ORDER BY quarter;
    """

    trend_state = pd.read_sql(
        text(trend_state_sql),
        engine,
        params={"state": state, "year": int(year), "util": util_type},
    )
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

    # -----------------------------
    # Top cost drivers by condition (therapeutic class proxy)
    # -----------------------------
    top_class_state_sql = """
    SELECT TOP 15
      LEFT(product_name_norm, CHARINDEX(' ', product_name_norm + ' ') - 1) AS thera_class,
      SUM(total_amount_reimbursed) AS total_reimbursed
    FROM dbo.sdud_analytics
    WHERE state = :state
      AND [year] = :year
      AND quarter = :quarter
      AND utilization_type = :util
    GROUP BY LEFT(product_name_norm, CHARINDEX(' ', product_name_norm + ' ') - 1)
    ORDER BY total_reimbursed DESC;
    """

    top_class_nat_sql = """
    SELECT TOP 15
      LEFT(product_name_norm, CHARINDEX(' ', product_name_norm + ' ') - 1) AS thera_class,
      SUM(total_amount_reimbursed) AS total_reimbursed
    FROM dbo.sdud_analytics
    WHERE state <> 'XX'
      AND [year] = :year
      AND quarter = :quarter
      AND utilization_type = :util
    GROUP BY LEFT(product_name_norm, CHARINDEX(' ', product_name_norm + ' ') - 1)
    ORDER BY total_reimbursed DESC;
    """

    top_state = pd.read_sql(text(top_class_state_sql), engine, params=params_state)
    top_state["scope"] = "State"

    if scope == "state_vs_national":
        top_nat = pd.read_sql(text(top_class_nat_sql), engine, params=params_nat)
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

        # ✅ FIXED INDENTATION (no extra indent here)
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

    # -----------------------------
    # Cost per Rx distribution + Top 1% spend share
    # -----------------------------
    cpp_state_sql = """
    SELECT
      (total_amount_reimbursed / NULLIF(number_of_prescriptions, 0)) AS cost_per_rx,
      number_of_prescriptions,
      total_amount_reimbursed
    FROM dbo.sdud_analytics
    WHERE state = :state
      AND [year] = :year
      AND quarter = :quarter
      AND utilization_type = :util
      AND number_of_prescriptions > 0
      AND total_amount_reimbursed IS NOT NULL;
    """

    cpp_nat_sql = """
    SELECT
      (total_amount_reimbursed / NULLIF(number_of_prescriptions, 0)) AS cost_per_rx,
      number_of_prescriptions,
      total_amount_reimbursed
    FROM dbo.sdud_analytics
    WHERE state <> 'XX'
      AND [year] = :year
      AND quarter = :quarter
      AND utilization_type = :util
      AND number_of_prescriptions > 0
      AND total_amount_reimbursed IS NOT NULL;
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
    )


if __name__ == "__main__":
    app.run(debug=True)