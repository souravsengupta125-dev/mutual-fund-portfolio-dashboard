# ============================================================
# MUTUAL FUND DASHBOARD
# STEP 1 - IMPORTS & DATA PREPARATION
# ============================================================

import pandas as pd
import numpy as np

# ------------------------------------------------------------
# File Location
# ------------------------------------------------------------

FILE_PATH = "sample transactions.xlsx"

# ------------------------------------------------------------
# Read Excel Sheets
# ------------------------------------------------------------

transactions = pd.read_excel(
    FILE_PATH,
    sheet_name="Transactions"
)

current = pd.read_excel(
    FILE_PATH,
    sheet_name="Current NAV and Units"
)

# ------------------------------------------------------------
# Display Basic Information
# ------------------------------------------------------------

print("="*60)
print("TRANSACTIONS")
print("="*60)

print(transactions.head())
print()

print(transactions.columns.tolist())
print()

print("="*60)
print("CURRENT HOLDINGS")
print("="*60)

print(current.head())
print()

print(current.columns.tolist())
print()

# ------------------------------------------------------------
# Remove Completely Blank Rows
# ------------------------------------------------------------

transactions.dropna(how='all', inplace=True)
current.dropna(how='all', inplace=True)

# ------------------------------------------------------------
# Remove Duplicate Rows
# ------------------------------------------------------------



# ------------------------------------------------------------
# Strip Spaces from Column Names
# ------------------------------------------------------------

transactions.columns = transactions.columns.str.strip()
current.columns = current.columns.str.strip()

# ------------------------------------------------------------
# Strip Spaces from Text Columns
# ------------------------------------------------------------

for col in transactions.select_dtypes(include='object'):
    transactions[col] = transactions[col].astype(str).str.strip()

for col in current.select_dtypes(include='object'):
    current[col] = current[col].astype(str).str.strip()

# ------------------------------------------------------------
# Convert Dates Automatically
# ------------------------------------------------------------

for col in transactions.columns:

    if "date" in col.lower():

        transactions[col] = pd.to_datetime(
            transactions[col],
            errors="coerce"
        )

# ------------------------------------------------------------
# Convert Numeric Columns
# ------------------------------------------------------------

numeric_cols_trans = ['Units', 'NAV', 'Amount']

for col in numeric_cols_trans:
    transactions[col] = (
        transactions[col]
        .astype(str)
        .str.replace(',', '', regex=False)
        .str.replace('₹', '', regex=False)
        .str.strip()
    )

    transactions[col] = pd.to_numeric(
        transactions[col],
        errors='coerce'
    )

numeric_cols_current = ['Current Units', 'Current NAV']

for col in numeric_cols_current:
    current[col] = (
        current[col]
        .astype(str)
        .str.replace(',', '', regex=False)
        .str.replace('₹', '', regex=False)
        .str.strip()
    )

    current[col] = pd.to_numeric(
        current[col],
        errors='coerce'
    )

transactions['Date'] = pd.to_datetime(
    transactions['Date'],
    errors='coerce'
)

# ------------------------------------------------------------
# Replace Infinite Values
# ------------------------------------------------------------

transactions.replace(
    [np.inf, -np.inf],
    np.nan,
    inplace=True
)

current.replace(
    [np.inf, -np.inf],
    np.nan,
    inplace=True
)

# ------------------------------------------------------------
# Reset Index
# ------------------------------------------------------------

transactions.reset_index(drop=True, inplace=True)
current.reset_index(drop=True, inplace=True)

# ------------------------------------------------------------
# Display Data Summary
# ------------------------------------------------------------

print("\n")
print("="*60)
print("TRANSACTIONS INFO")
print("="*60)

print(transactions.info())

print("\n")

print("="*60)
print("CURRENT INFO")
print("="*60)

print(current.info())

# ------------------------------------------------------------
# Missing Values
# ------------------------------------------------------------

print("\n")
print("="*60)
print("MISSING VALUES")
print("="*60)

print("\nTransactions")

print(transactions.isnull().sum())

print("\nCurrent Holdings")

print(current.isnull().sum())

# ------------------------------------------------------------
# Shapes
# ------------------------------------------------------------

print("\n")
print("="*60)
print("DATA SIZE")
print("="*60)

print("Transactions :", transactions.shape)

print("Current Holdings :", current.shape)

print("\n")

print("="*60)
print("STEP 1 COMPLETED SUCCESSFULLY")
print("="*60)

# ============================================================
# Standardize Transaction Types
# ============================================================

transactions["Transaction Type"] = (
    transactions["Transaction Type"]
    .str.upper()
    .str.strip()
)

print("\nUnique Transaction Types\n")
print(sorted(transactions["Transaction Type"].unique()))

# ============================================================
# STEP 2 - PORTFOLIO ENGINE
# ============================================================

# ------------------------------------------------------------
# Split Purchase & Redemption Transactions
# ------------------------------------------------------------

purchase_df = transactions[
    transactions["Transaction Type"] == "PURCHASE"
].copy()

redeem_df = transactions[
    transactions["Transaction Type"] == "REDEEM"
].copy()

# ------------------------------------------------------------
# Purchase Summary
# ------------------------------------------------------------

purchase_summary = (
    purchase_df
    .groupby("Scheme Name", as_index=False)
    .agg(
        Purchased_Units=("Units", "sum"),
        Amount_Invested=("Amount", "sum")
    )
)

# ------------------------------------------------------------
# Redemption Summary
# ------------------------------------------------------------

redeem_summary = (
    redeem_df
    .groupby("Scheme Name", as_index=False)
    .agg(
        Redeemed_Units=("Units", "sum"),
        Amount_Redeemed=("Amount", "sum")
    )
)

# ------------------------------------------------------------
# Merge Purchase & Redemption
# ------------------------------------------------------------

portfolio = purchase_summary.merge(
    redeem_summary,
    on="Scheme Name",
    how="outer"
)

portfolio.fillna(0, inplace=True)

# ------------------------------------------------------------
# Net Units
# ------------------------------------------------------------

portfolio["Net Units"] = (
    portfolio["Purchased_Units"]
    - portfolio["Redeemed_Units"]
)

# ------------------------------------------------------------
# Merge Current Holdings
# ------------------------------------------------------------

portfolio = portfolio.merge(
    current,
    on="Scheme Name",
    how="left"
)

portfolio["Current Units"] = portfolio["Net Units"]
portfolio["Current NAV"] = portfolio["Current NAV"].fillna(0)

# ------------------------------------------------------------
# Current Value
# ------------------------------------------------------------

portfolio["Current Value"] = (
    portfolio["Current Units"]
    * portfolio["Current NAV"]
)

# ------------------------------------------------------------
# Cost Per Unit
# ------------------------------------------------------------

portfolio["Average Cost"] = (
    portfolio["Amount_Invested"]
    / portfolio["Purchased_Units"]
)

portfolio["Average Cost"] = (
    portfolio["Average Cost"]
    .replace([np.inf, -np.inf], 0)
    .fillna(0)
)

# ------------------------------------------------------------
# Cost of Remaining Units
# ------------------------------------------------------------

portfolio["Cost Value"] = (
    portfolio["Current Units"]
    * portfolio["Average Cost"]
)

# ------------------------------------------------------------
# Profit / Loss
# ------------------------------------------------------------

portfolio["Profit"] = (
    portfolio["Current Value"]
    - portfolio["Cost Value"]
)

portfolio["Return %"] = np.where(
    portfolio["Cost Value"] > 0,
    portfolio["Profit"] / portfolio["Cost Value"] * 100,
    0
)

# ------------------------------------------------------------
# Portfolio Weight
# ------------------------------------------------------------

total_value = portfolio["Current Value"].sum()

portfolio["Portfolio %"] = np.where(
    total_value > 0,
    portfolio["Current Value"] / total_value * 100,
    0
)

# ------------------------------------------------------------
# Sort by Current Value
# ------------------------------------------------------------

portfolio = (
    portfolio
    .sort_values(
        by="Current Value",
        ascending=False
    )
    .reset_index(drop=True)
)

# ------------------------------------------------------------
# Portfolio Summary
# ------------------------------------------------------------

print("\n")
print("=" * 80)
print("PORTFOLIO SUMMARY")
print("=" * 80)

print(f"Funds                : {len(portfolio)}")
print(f"Total Invested       : ₹ {portfolio['Amount_Invested'].sum():,.2f}")
print(f"Total Redeemed       : ₹ {portfolio['Amount_Redeemed'].sum():,.2f}")
print(f"Current Value        : ₹ {portfolio['Current Value'].sum():,.2f}")
print(f"Cost Value           : ₹ {portfolio['Cost Value'].sum():,.2f}")
print(f"Overall Profit       : ₹ {portfolio['Profit'].sum():,.2f}")

if portfolio["Cost Value"].sum() > 0:
    print(
        f"Overall Return %     : "
        f"{portfolio['Profit'].sum()/portfolio['Cost Value'].sum()*100:.2f}%"
    )
else:
    print("Overall Return %     : 0.00%")

print("=" * 80)

# ------------------------------------------------------------
# Display Portfolio
# ------------------------------------------------------------

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", None)

print("\nMASTER PORTFOLIO TABLE\n")

print(
    portfolio[
        [
            "Scheme Name",
            "Purchased_Units",
            "Redeemed_Units",
            "Current Units",
            "Amount_Invested",
            "Amount_Redeemed",
            "Average Cost",
            "Current NAV",
            "Cost Value",
            "Current Value",
            "Profit",
            "Return %",
            "Portfolio %"
        ]
    ]
)

# ============================================================
# STEP 3 - XIRR, IRR & PORTFOLIO METRICS
# ============================================================

from scipy.optimize import brentq

# ------------------------------------------------------------
# Create Cash Flow Table
# ------------------------------------------------------------

cashflows = transactions.copy()

cashflows["Cash Flow"] = np.where(
    cashflows["Transaction Type"] == "PURCHASE",
    -cashflows["Amount"],
    cashflows["Amount"]
)

# ------------------------------------------------------------
# Add Current Portfolio Value as Final Cash Inflow
# ------------------------------------------------------------

today = pd.Timestamp.today().normalize()

final_cf = pd.DataFrame({
    "Scheme Name": ["Portfolio"],
    "Transaction Type": ["CURRENT_VALUE"],
    "Units": [0],
    "NAV": [0],
    "Amount": [portfolio["Current Value"].sum()],
    "Date": [today],
    "Cash Flow": [portfolio["Current Value"].sum()]
})

cashflows = pd.concat(
    [cashflows, final_cf],
    ignore_index=True
)

cashflows = cashflows.sort_values("Date")

# ------------------------------------------------------------
# XIRR Function
# ------------------------------------------------------------

def xirr(cf):

    cf = cf.sort_values("Date").copy()

    dates = pd.to_datetime(cf["Date"]).tolist()
    amounts = pd.to_numeric(cf["Cash Flow"]).tolist()

    first_date = dates[0]

    def npv(rate):
        return sum(
            amt /
            ((1 + rate) ** ((dt - first_date).days / 365))
            for amt, dt in zip(amounts, dates)
        )

    try:
        return brentq(
            npv,
            -0.999999,
            1000,
            maxiter=1000
        )

    except:
        return np.nan

# ------------------------------------------------------------
# Portfolio XIRR
# ------------------------------------------------------------

portfolio_xirr = xirr(cashflows)

# ------------------------------------------------------------
# Portfolio IRR
# ------------------------------------------------------------

monthly_cf = (
    cashflows
    .set_index("Date")
    .resample("ME")["Cash Flow"]
    .sum()
)

try:

    portfolio_irr = np.irr(monthly_cf.values)

except:

    portfolio_irr = np.nan

# ------------------------------------------------------------
# Fund-wise XIRR
# ------------------------------------------------------------

fund_xirr = []

for fund in portfolio["Scheme Name"]:

    cf = transactions[
        transactions["Scheme Name"] == fund
    ].copy()

    cf["Cash Flow"] = np.where(
        cf["Transaction Type"] == "PURCHASE",
        -cf["Amount"],
        cf["Amount"]
    )

    current_value = portfolio.loc[
        portfolio["Scheme Name"] == fund,
        "Current Value"
    ].values[0]

    if current_value > 0:

        temp = pd.DataFrame({

            "Scheme Name":[fund],
            "Transaction Type":["CURRENT"],
            "Units":[0],
            "NAV":[0],
            "Amount":[current_value],
            "Date":[today],
            "Cash Flow":[current_value]

        })

        cf = pd.concat([cf, temp], ignore_index=True)

    cf = cf.sort_values("Date").reset_index(drop=True)

    if (cf["Cash Flow"] < 0).any() and (cf["Cash Flow"] > 0).any():
        fund_xirr.append(xirr(cf) * 100)
    else:
        fund_xirr.append(np.nan)

portfolio["XIRR %"] = np.round(fund_xirr, 2)
# ------------------------------------------------------------
# Portfolio Statistics
# ------------------------------------------------------------

total_invested = portfolio["Amount_Invested"].sum()

total_redeemed = portfolio["Amount_Redeemed"].sum()

current_value = portfolio["Current Value"].sum()

cost_value = portfolio["Cost Value"].sum()

profit = portfolio["Profit"].sum()

absolute_return = 0

if cost_value > 0:

    absolute_return = (profit / cost_value) * 100

# ------------------------------------------------------------
# Top 5 Best Funds
# ------------------------------------------------------------

top5 = portfolio.sort_values(

    "Return %",

    ascending=False

).head(5)

# ------------------------------------------------------------
# Bottom 5 Funds
# ------------------------------------------------------------

bottom5 = portfolio.sort_values(

    "Return %"

).head(5)

# ------------------------------------------------------------
# Print Summary
# ------------------------------------------------------------

print("\n")

print("=" * 80)

print("PORTFOLIO PERFORMANCE")

print("=" * 80)

print(f"Total Invested      : ₹ {total_invested:,.2f}")

print(f"Total Redeemed      : ₹ {total_redeemed:,.2f}")

print(f"Current Value       : ₹ {current_value:,.2f}")

print(f"Cost Value          : ₹ {cost_value:,.2f}")

print(f"Profit              : ₹ {profit:,.2f}")

print(f"Absolute Return     : {absolute_return:.2f}%")

print(f"Portfolio XIRR      : {portfolio_xirr*100:.2f}%")

if pd.notna(portfolio_irr):

    print(f"Portfolio IRR       : {portfolio_irr*100:.2f}%")

else:

    print("Portfolio IRR       : NA")

print("=" * 80)

# ------------------------------------------------------------
# Top Performing Funds
# ------------------------------------------------------------

print("\n")

print("=" * 80)

print("TOP 5 PERFORMERS")

print("=" * 80)

print(

    top5[

        [

            "Scheme Name",

            "Current Value",

            "Profit",

            "Return %",

            "XIRR %"

        ]

    ]

)

# ------------------------------------------------------------
# Bottom Performing Funds
# ------------------------------------------------------------

print("\n")

print("=" * 80)

print("BOTTOM 5 PERFORMERS")

print("=" * 80)

print(

    bottom5[

        [

            "Scheme Name",

            "Current Value",

            "Profit",

            "Return %",

            "XIRR %"

        ]

    ]

)

# ------------------------------------------------------------
# Save Master Portfolio
# ------------------------------------------------------------

portfolio.to_csv(

    "portfolio_master.csv",

    index=False

)

print("\nportfolio_master.csv created successfully.")

# ============================================================
# STEP 4 - ASSET ALLOCATION & FUND ANALYTICS
# ============================================================

import plotly.express as px
import plotly.graph_objects as go

# ------------------------------------------------------------
# Create Dashboard DataFrame
# ------------------------------------------------------------

dashboard = portfolio.copy()

# ------------------------------------------------------------
# Holding Weight
# ------------------------------------------------------------

dashboard["Holding Weight %"] = (
    dashboard["Current Value"]
    / dashboard["Current Value"].sum()
    * 100
)

# ------------------------------------------------------------
# Profit Contribution
# ------------------------------------------------------------

dashboard["Profit Contribution %"] = np.where(
    dashboard["Profit"].sum() != 0,
    dashboard["Profit"] /
    dashboard["Profit"].sum() * 100,
    0
)

# ------------------------------------------------------------
# Gain/Loss Category
# ------------------------------------------------------------

dashboard["Status"] = np.where(
    dashboard["Profit"] >= 0,
    "Profit",
    "Loss"
)

# ------------------------------------------------------------
# Top Holdings
# ------------------------------------------------------------

top_holdings = (
    dashboard
    .sort_values("Current Value", ascending=False)
    .head(10)
)

# ------------------------------------------------------------
# Top Gainers
# ------------------------------------------------------------

top_gainers = (
    dashboard
    .sort_values("Return %", ascending=False)
    .head(10)
)

# ------------------------------------------------------------
# Top Losers
# ------------------------------------------------------------

top_losers = (
    dashboard
    .sort_values("Return %")
    .head(10)
)

# ------------------------------------------------------------
# Highest XIRR
# ------------------------------------------------------------

top_xirr = (
    dashboard
    .sort_values("XIRR %", ascending=False)
    .head(10)
)

# ------------------------------------------------------------
# Lowest XIRR
# ------------------------------------------------------------

bottom_xirr = (
    dashboard
    .sort_values("XIRR %")
    .head(10)
)

# ------------------------------------------------------------
# Portfolio Statistics
# ------------------------------------------------------------

print("\n")

print("="*80)

print("PORTFOLIO ANALYTICS")

print("="*80)

print(f"Number of Funds        : {len(dashboard)}")

print(f"Largest Holding        : {dashboard.iloc[0]['Scheme Name']}")

print(f"Largest Holding Value  : ₹ {dashboard.iloc[0]['Current Value']:,.2f}")

print(f"Smallest Holding       : {dashboard.iloc[-1]['Scheme Name']}")

print(f"Smallest Holding Value : ₹ {dashboard.iloc[-1]['Current Value']:,.2f}")

print(f"Average Return         : {dashboard['Return %'].mean():.2f}%")

print(f"Median Return          : {dashboard['Return %'].median():.2f}%")

print(f"Highest Return         : {dashboard['Return %'].max():.2f}%")

print(f"Lowest Return          : {dashboard['Return %'].min():.2f}%")

print("="*80)

# ------------------------------------------------------------
# Pie Chart
# ------------------------------------------------------------

fig = px.pie(

    dashboard,

    names="Scheme Name",

    values="Current Value",

    title="Portfolio Allocation"

)



# ------------------------------------------------------------
# Treemap
# ------------------------------------------------------------

fig = px.treemap(

    dashboard,

    path=["Scheme Name"],

    values="Current Value",

    color="Return %"

)



# ------------------------------------------------------------
# Current Value
# ------------------------------------------------------------

fig = px.bar(

    top_holdings,

    x="Scheme Name",

    y="Current Value",

    title="Top Holdings"

)

fig.update_layout(

    xaxis_tickangle=-60

)



# ------------------------------------------------------------
# Profit
# ------------------------------------------------------------

fig = px.bar(

    dashboard.sort_values("Profit", ascending=False),

    x="Scheme Name",

    y="Profit",

    color="Status",

    title="Profit / Loss"

)

fig.update_layout(

    xaxis_tickangle=-60

)



# ------------------------------------------------------------
# Return %
# ------------------------------------------------------------

fig = px.bar(

    dashboard.sort_values("Return %", ascending=False),

    x="Scheme Name",

    y="Return %",

    color="Status",

    title="Fund Returns"

)

fig.update_layout(

    xaxis_tickangle=-60

)



# ------------------------------------------------------------
# XIRR
# ------------------------------------------------------------

fig = px.bar(

    dashboard.sort_values("XIRR %", ascending=False),

    x="Scheme Name",

    y="XIRR %",

    title="Fund-wise XIRR"

)

fig.update_layout(

    xaxis_tickangle=-60

)



# ------------------------------------------------------------
# Save Analytics
# ------------------------------------------------------------

dashboard.to_csv(

    "dashboard_data.csv",

    index=False

)

print("\nDashboard data exported.")

# ------------------------------------------------------------
# Save Rankings
# ------------------------------------------------------------

top_holdings.to_csv(

    "top_holdings.csv",

    index=False

)

top_gainers.to_csv(

    "top_gainers.csv",

    index=False

)

top_losers.to_csv(

    "top_losers.csv",

    index=False

)

top_xirr.to_csv(

    "top_xirr.csv",

    index=False

)

bottom_xirr.to_csv(

    "bottom_xirr.csv",

    index=False

)

print("Ranking files exported.")

# ============================================================
# STEP 5A - DASHBOARD LAYOUT
# Cards + Tabs + Graphs + Holdings Table
# ============================================================

import dash
from dash import dcc, html, dash_table
from dash.dash_table.Format import Format, Scheme
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import webbrowser
from threading import Timer

# ------------------------------------------------------------
# CREATE DASH APP
# ------------------------------------------------------------

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP
    ]
)
server = app.server
# ------------------------------------------------------------
# PREMIUM DASHBOARD THEME
# ------------------------------------------------------------

BG = "#F4F7FB"
CARD = "#FFFFFF"
NAVY = "#172033"
NAVY_2 = "#202B3F"
TEXT = "#172033"
MUTED = "#718096"
BORDER = "#E5EAF1"
BLUE = "#4F46E5"
BLUE_LIGHT = "#EEF2FF"
GREEN = "#16A34A"
GREEN_LIGHT = "#ECFDF3"
RED = "#DC2626"
RED_LIGHT = "#FEF2F2"
ORANGE = "#F59E0B"
ORANGE_LIGHT = "#FFF7ED"
PURPLE = "#7C3AED"
TEAL = "#0F766E"

# ------------------------------------------------------------
# SAFE DATA COPIES
# ------------------------------------------------------------

dash_portfolio = portfolio.copy()

# ------------------------------------------------------------
# FORMAT NUMBERS
# ------------------------------------------------------------

def money(x):
    try:
        return f"₹{float(x):,.0f}"
    except:
        return "₹0"

def pct(x):
    try:
        return f"{float(x):,.2f}%"
    except:
        return "0.00%"

# ------------------------------------------------------------
# PORTFOLIO KPIs
# ------------------------------------------------------------

# ------------------------------------------------------------
# PORTFOLIO VALUE / INVESTMENT / REDEMPTION
# ------------------------------------------------------------

total_current = dash_portfolio["Current Value"].sum()

# Gross amount invested through PURCHASE transactions
total_invested = transactions.loc[
    transactions["Transaction Type"] == "PURCHASE",
    "Amount"
].sum()

# Total amount received through REDEEM transactions
total_redeemed = transactions.loc[
    transactions["Transaction Type"] == "REDEEM",
    "Amount"
].sum()

# Net capital invested after redemptions
net_invested = total_invested - total_redeemed

# Profit against net capital still invested
total_profit = total_current - net_invested

# Absolute return %
if net_invested != 0:
    total_return = (total_profit / net_invested) * 100
else:
    total_return = 0

portfolio_xirr_value = globals().get("portfolio_xirr", np.nan)

if pd.notna(portfolio_xirr_value):
    portfolio_xirr_display = portfolio_xirr_value * 100
else:
    portfolio_xirr_display = np.nan

fund_count = len(dash_portfolio)

# ------------------------------------------------------------
# KPI CARD
# ------------------------------------------------------------

def kpi_card(title, value, subtitle="", accent=BLUE, icon=""):

    return html.Div(
        [

            html.Div(
                [
                    html.Div(
                        icon,
                        style={
                            "width": "36px",
                            "height": "36px",
                            "borderRadius": "10px",
                            "backgroundColor": accent,
                            "color": "white",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "fontSize": "16px",
                            "fontWeight": "800"
                        }
                    ),

                    html.Div(
                        title,
                        style={
                            "fontSize": "10px",
                            "fontWeight": "700",
                            "color": MUTED,
                            "letterSpacing": "0.5px",
                            "textTransform": "uppercase",
                            "marginLeft": "10px"
                        }
                    )
                ],

                style={
                    "display": "flex",
                    "alignItems": "center"
                }
            ),

            html.Div(
                value,
                style={
                    "fontSize": "22px",
                    "fontWeight": "800",
                    "color": TEXT,
                    "marginTop": "13px",
                    "letterSpacing": "-0.5px"
                }
            ),

            html.Div(
                subtitle,
                style={
                    "fontSize": "10px",
                    "color": MUTED,
                    "marginTop": "4px"
                }
            )

        ],

        style={
            "backgroundColor": CARD,
            "border": f"1px solid {BORDER}",
            "borderRadius": "14px",
            "padding": "16px",
            "boxShadow": "0 3px 12px rgba(15,23,42,0.04)",
            "minHeight": "112px"
        }
    )
# ============================================================
# PREMIUM GRAPH STYLE
# ============================================================

def premium_graph(fig, height=330):

    fig.update_layout(
        template="plotly_white",

        paper_bgcolor=CARD,
        plot_bgcolor=CARD,

        font={
            "family": "Inter, Segoe UI, Arial",
            "color": TEXT,
            "size": 12
        },

        title={
            "font": {
                "size": 16,
                "color": TEXT,
                "family": "Inter, Segoe UI, Arial"
            },
            "x": 0.02,
            "xanchor": "left",
            "y": 0.96
        },

        height=height,

        margin={
            "l": 55,
            "r": 25,
            "t": 55,
            "b": 55
        },

        hoverlabel={
            "bgcolor": NAVY,
            "font": {
                "color": "white",
                "size": 12
            },
            "bordercolor": NAVY
        },

        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.01,
            "xanchor": "right",
            "x": 1
        },

        xaxis={
            "showgrid": False,
            "zeroline": False,
            "showline": False,
            "tickfont": {
                "color": MUTED,
                "size": 11
            }
        },

        yaxis={
            "showgrid": True,
            "gridcolor": "#EDF1F7",
            "zeroline": False,
            "showline": False,
            "tickfont": {
                "color": MUTED,
                "size": 11
            }
        }
    )

    fig.update_traces(
        marker_line_width=0
    )

    return fig
# ============================================================
# PREMIUM SECTION STYLE
# ============================================================

SECTION_STYLE = {
    "backgroundColor": CARD,
    "border": f"1px solid {BORDER}",
    "borderRadius": "14px",
    "boxShadow": "0 3px 12px rgba(15,23,42,0.04)",
    "overflow": "hidden"
}
PAGE_STYLE = {
    "backgroundColor": BG,
    "minHeight": "100vh",
    "padding": "20px 28px 40px 28px",
    "fontFamily": "Inter, Segoe UI, Arial, sans-serif",
    "color": TEXT
}
# ------------------------------------------------------------
# HOLDINGS TABLE COLUMNS
# ------------------------------------------------------------

preferred_columns = [
    "Scheme Name",
    "Current Units",
    "Current NAV",
    "Invested Amount",
    "Current Value",
    "Profit",
    "Return %",
    "XIRR %"
]

table_columns = [
    c for c in preferred_columns
    if c in dash_portfolio.columns
]

def get_column_format(col):
    if col in [
        "Invested Amount",
        "Cost Value",
        "Current Value",
        "Amount Invested",
        "Profit"
    ]:
        return Format(
            precision=2,
            scheme=Scheme.fixed
        ).group(True)

    elif col in [
        "Current Units",
        "Current NAV"
    ]:
        return Format(
            precision=2,
            scheme=Scheme.fixed
        )

    elif col in [
        "Return %",
        "XIRR %",
        "Portfolio Weight"
    ]:
        return Format(
            precision=2,
            scheme=Scheme.fixed
        )

    return None    

holdings_table = dash_table.DataTable(
    id="holdings-table",

    data=dash_portfolio[table_columns].to_dict("records"),
    
    
    columns=[
    {
        "name": col,
        "id": col,
        "type": "numeric",
        "format": get_column_format(col)
        
    }
        if get_column_format(col) is not None
        else {
        "name": col,
        "id": col
    }
    for col in table_columns
    ],
    
    


sort_action="native",
filter_action="native",
page_action="native",
page_size=15,

style_table={
    "width": "100%",
    "overflowX": "auto",
    "borderRadius": "12px",
    "border": f"1px solid {BORDER}",
    "backgroundColor": CARD
},

style_header={
    "backgroundColor": NAVY,
    "color": "white",
    "fontWeight": "700",
    "fontSize": "11px",
    "textAlign": "center",
    "padding": "13px 10px",
    "border": "none",
    "whiteSpace": "nowrap"
},

style_cell={
    "padding": "11px 10px",
    "fontSize": "12px",
    "fontFamily": "Inter, Segoe UI, Arial",
    "color": TEXT,
    "minWidth": "90px",
    "backgroundColor": CARD,
    "border": f"1px solid {BORDER}",
    "textAlign": "right",
    "height": "42px",
    "whiteSpace": "nowrap"
},

style_cell_conditional=[

    {
        "if": {
            "column_id": "Scheme Name"
        },
        "textAlign": "left",
        "width": "24%",
        "minWidth": "300px",
        "maxWidth": "380px",
        "fontWeight": "600",
        "paddingLeft": "10px"
    },

    {
        "if": {
            "column_id": "Current Units"
        },
        "width": "12%",
        "textAlign": "right"
    },

    {
        "if": {
            "column_id": "Current NAV"
        },
        "width": "10%",
        "textAlign": "right"
    },

    {
        "if": {
            "column_id": "Current Value"
        },
        "width": "15%",
        "textAlign": "right"
    },

    {
        "if": {
            "column_id": "Profit"
        },
        "width": "13%",
        "textAlign": "right"
    },

    {
        "if": {
            "column_id": "Return %"
        },
        "width": "10%",
        "textAlign": "right"
    },

    {
        "if": {
            "column_id": "XIRR %"
        },
        "width": "10%",
        "textAlign": "right"
    }
],
)



style_data_conditional=[
        {
            "if": {
                "filter_query": "{Profit} > 0",
                "column_id": "Profit"
            },
            "color": GREEN,
            "fontWeight": "600"
        },
        {
            "if": {
                "filter_query": "{Profit} < 0",
                "column_id": "Profit"
            },
            "color": RED,
            "fontWeight": "600"
        },
        {
            "if": {
                "filter_query": "{Return %} > 0",
                "column_id": "Return %"
            },
            "color": GREEN,
            "fontWeight": "600"
        },
        {
            "if": {
                "filter_query": "{Return %} < 0",
                "column_id": "Return %"
            },
            "color": RED,
            "fontWeight": "600"
        }
    ]
        

# ------------------------------------------------------------
# ASSET ALLOCATION
# ------------------------------------------------------------

asset_fig = go.Figure()

if "Asset Class" in dash_portfolio.columns:

    asset_data = (
        dash_portfolio
        .groupby("Asset Class", as_index=False)["Current Value"]
        .sum()
    )

    asset_fig = px.pie(
        asset_data,
        names="Asset Class",
        values="Current Value",
        hole=0.45,
        title="Asset Allocation"
    )

else:

    asset_fig.add_annotation(
        text="Asset Class data not available",
        showarrow=False
    )

asset_fig.update_layout(
    template="plotly_white",
    margin=dict(l=20, r=20, t=50, b=20),
    legend_title=""
)


# ============================================================
# STEP 5A - DASHBOARD LAYOUT
# ============================================================



# ------------------------------------------------------------
# TOP PERFORMERS
# ------------------------------------------------------------

performer_fig = go.Figure()

if "Return %" in dash_portfolio.columns:

    top_performers = (
        dash_portfolio
        .sort_values("XIRR %", ascending=False)
        .head(10)
        .sort_values("XIRR %")
    )

    performer_fig = px.bar(
        top_performers,
        x="XIRR %",
        y="Scheme Name",
        orientation="h",
        title="Top 10 Performing Funds"
    )

else:

    performer_fig.add_annotation(
        text="XIRR % data not available",
        showarrow=False
    )

performer_fig.update_layout(
    template="plotly_white",
    margin=dict(l=20, r=20, t=50, b=20),
    yaxis_title="",
    xaxis_title="XIRR %"
)

# ------------------------------------------------------------
# BOTTOM PERFORMERS
# ------------------------------------------------------------

bottom_fig = go.Figure()

if "XIRR %" in dash_portfolio.columns:

    bottom_performers = (
        dash_portfolio
        .sort_values("XIRR %", ascending=True)
        .head(10)
        .sort_values("XIRR %", ascending=False)
    )

    bottom_fig = px.bar(
        bottom_performers,
        x="XIRR %",
        y="Scheme Name",
        orientation="h",
        title="Bottom 10 Performing Funds"
    )

else:

    bottom_fig.add_annotation(
        text="XIRR % data not available",
        showarrow=False
    )

bottom_fig.update_layout(
    template="plotly_white",
    margin=dict(l=20, r=20, t=50, b=20),
    yaxis_title="",
    xaxis_title="XIRR %"
)







# ------------------------------------------------------------
# SECTION CARD
# ------------------------------------------------------------

def section_card(component):

    return html.Div(
        component,
        style={
            "backgroundColor": CARD,
            "borderRadius": "12px",
            "padding": "15px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
            "marginBottom": "20px"
        }
    )
# ============================================================
# STEP 6A - ASSET SPLIT / MARKET CAP / AMC CLASSIFICATION
# ============================================================

# ------------------------------------------------------------
# ASSET CLASS MAPPING
# ------------------------------------------------------------

ASSET_CLASS = {

    "Mutual Fund 1":"Hybrid",
    "Mutual Fund 2":"Equity",
    "Mutual Fund 3":"Debt",
    "Mutual Fund 4":"Equity",
    "Mutual Fund 5":"Hybrid",
    "Mutual Fund 6":"Debt",
    "Mutual Fund 7":"Equity",
    "Mutual Fund 8":"Hybrid",
    "Mutual Fund 9":"Equity",
    "Mutual Fund 10":"Equity",
    "Mutual Fund 11":"Equity",
    "Mutual Fund 12":"Debt",
    "Mutual Fund 13":"Debt",
    "Mutual Fund 14":"Multi Asset",
    "Mutual Fund 15":"Debt",
    "Mutual Fund 16":"Equity",
    "Mutual Fund 17":"Equity",
    "Mutual Fund 18":"Equity",
    "Mutual Fund 19":"Debt",
    "Mutual Fund 20":"Equity",
    

}

# ------------------------------------------------------------
# MARKET CAP MAPPING
# ------------------------------------------------------------

MARKET_CAP = {

    "Mutual Fund 1":  "Hybrid",
    "Mutual Fund 2":  "Small Cap",
    "Mutual Fund 3":  "Debt",
    "Mutual Fund 4":  "Small Cap",
    "Mutual Fund 5":  "Hybrid",
    "Mutual Fund 6":  "Debt",   
    "Mutual Fund 7":  "Small Cap",
    "Mutual Fund 8":  "Hybrid",
    "Mutual Fund 9":  "Small Cap",
    "Mutual Fund 10":  "Small Cap",
    "Mutual Fund 11":  "Flexi Cap",
    "Mutual Fund 12":  "Debt",
    "Mutual Fund 13":  "Debt",
    "Mutual Fund 14":  "Multi Asset",
    "Mutual Fund 15":  "Debt",
    "Mutual Fund 16":  "Debt",
    "Mutual Fund 17":  "Small Cap",
    "Mutual Fund 18":  "Large Cap",
    "Mutual Fund 19":  "Small Cap",
    "Mutual Fund 20":  "Mid Cap",


}

# ------------------------------------------------------------
# AMC MAPPING
# ------------------------------------------------------------

dashboard["AMC"] = (

    dashboard["Scheme Name"]

    .str.split()

    .str[0]

)

dashboard["Asset Class"] = (

    dashboard["Scheme Name"]

    .map(ASSET_CLASS)

    .fillna("Others")

)

dashboard["Market Cap"] = (

    dashboard["Scheme Name"]

    .map(MARKET_CAP)

    .fillna("Others")

)


# ------------------------------------------------------------
# ASSET SUMMARY
# ------------------------------------------------------------

asset_summary = (

    dashboard

    .groupby("Asset Class",as_index=False)

    ["Current Value"]

    .sum()

)

asset_summary["Weight %"] = (

    asset_summary["Current Value"]

    /

    asset_summary["Current Value"].sum()

    *100

)

# ------------------------------------------------------------
# MARKET CAP SUMMARY
# ------------------------------------------------------------

marketcap_summary = (

    dashboard

    .groupby("Market Cap",as_index=False)

    ["Current Value"]

    .sum()

)

marketcap_summary["Weight %"] = (

    marketcap_summary["Current Value"]

    /

    marketcap_summary["Current Value"].sum()

    *100

)

# ------------------------------------------------------------
# AMC SUMMARY
# ------------------------------------------------------------

amc_summary = (

    dashboard

    .groupby("AMC",as_index=False)

    ["Current Value"]

    .sum()

)

amc_summary["Weight %"] = (

    amc_summary["Current Value"]

    /

    amc_summary["Current Value"].sum()

    *100

)
# ============================================================
# STEP 6B - NEW DASHBOARD CHARTS
# (Place AFTER Step 6A and BEFORE Step 5B)
# ============================================================

import plotly.express as px

# ------------------------------------------------------------
# ASSET ALLOCATION
# ------------------------------------------------------------

asset_fig = px.pie(

    asset_summary,

    names="Asset Class",

    values="Current Value",

    hole=0.45,

    title="Asset Allocation"

)

asset_fig.update_layout(

    title_x=0.5,

    template="plotly_white"

)

# ------------------------------------------------------------
# MARKET CAP ALLOCATION
# ------------------------------------------------------------

marketcap_summary_filtered = marketcap_summary[
    marketcap_summary["Market Cap"].isin(
        ["Small Cap", "Mid Cap", "Large Cap","Flexi Cap"]
    )
].copy()

marketcap_fig = px.pie(
    marketcap_summary_filtered,
    names="Market Cap",
    values="Current Value",
    hole=0.45,
    title="Market Cap Allocation"
)

marketcap_fig.update_layout(

    title_x=0.5,

    template="plotly_white"

)

# ============================================================
# STEP 6C - PORTFOLIO ANALYTICS
# (Place AFTER Step 6B and BEFORE Step 5B)
# ============================================================

# ------------------------------------------------------------
# MONTHLY INVESTMENT
# ------------------------------------------------------------

monthly_purchase = (

    transactions

    [

        transactions["Transaction Type"] == "PURCHASE"

    ]

    .groupby(

        pd.Grouper(

            key="Date",

            freq="ME"

        )

    )["Amount"]

    .sum()

    .reset_index()

)

monthly_purchase.columns = [

    "Month",

    "Investment"

]

# ------------------------------------------------------------
# MONTHLY PURCHASE GRAPH
# ------------------------------------------------------------

purchase_fig = px.bar(
    monthly_purchase,
    x="Month",
    y="Investment",
    title="Monthly Purchases"
)

purchase_fig.update_layout(
    template="plotly_white",
    title_x=0.5,
    xaxis_title="Month",
    yaxis_title="Amount Invested",
    hovermode="x unified"
)

# ------------------------------------------------------------
# MONTHLY REDEMPTION
# ------------------------------------------------------------

monthly_redemption = (

    transactions

    [

        transactions["Transaction Type"] == "REDEEM"

    ]

    .groupby(

        pd.Grouper(

            key="Date",

            freq="ME"

        )

    )["Amount"]

    .sum()

    .reset_index()

)

monthly_redemption.columns = [

    "Month",

    "Redemption"

]

# ------------------------------------------------------------
# MONTHLY REDEMPTION CHART
# ------------------------------------------------------------

redemption_fig = px.bar(
    monthly_redemption,
    x="Month",
    y="Redemption",
    title="Monthly Redemptions"
)

redemption_fig.update_layout(
    template="plotly_white",
    title_x=0.5,
    xaxis_title="Month",
    yaxis_title="Amount Redeemed",
    hovermode="x unified"
)

# ------------------------------------------------------------
# MONTHLY NET CASHFLOW
# ------------------------------------------------------------

cashflow = (

    monthly_purchase

    .merge(

        monthly_redemption,

        how="outer",

        on="Month"

    )

    .fillna(0)

)

cashflow["Net Investment"] = (

    cashflow["Investment"]

    -

    cashflow["Redemption"]

)

# ------------------------------------------------------------
# PORTFOLIO GROWTH
# ------------------------------------------------------------

portfolio_growth = (
    transactions[
        transactions["Transaction Type"] == "PURCHASE"
    ]
    .groupby(
        pd.Grouper(
            key="Date",
            freq="ME"
        )
    )["Amount"]
    .sum()
    .cumsum()
    .reset_index()
)

portfolio_growth.columns = [
    "Month",
    "Amount Invested"
    
]
portfolio_growth["Current Value"] = current_value    
# ------------------------------------------------------------
# PORTFOLIO GROWTH
# ------------------------------------------------------------

growth_fig = go.Figure()

if "portfolio_growth" in globals():

    growth_data = portfolio_growth.copy()

    if len(growth_data.columns) >= 2:

        date_col = growth_data.columns[0]
        value_col = growth_data.columns[-1]

        growth_fig = px.line(
            growth_data,
            x=date_col,
            y=value_col,
            title="Portfolio Growth"
        )

else:

    growth_fig.add_annotation(
        text="Portfolio Growth data not available",
        showarrow=False
    )

growth_fig.update_layout(
    template="plotly_white",
    margin=dict(l=20, r=20, t=50, b=20)
)

# ------------------------------------------------------------
# SIP VS LUMPSUM
# ------------------------------------------------------------

sip_transactions = (

    transactions

    [

        transactions["Amount"] <= 10000

    ]

)

lumpsum_transactions = (

    transactions

    [

        transactions["Amount"] > 10000

    ]

)

sip_summary = pd.DataFrame(

    {

        "Category":[

            "SIP",

            "Lumpsum"

        ],

        "Transactions":[

            len(sip_transactions),

            len(lumpsum_transactions)

        ],

        "Amount":[

            sip_transactions["Amount"].sum(),

            lumpsum_transactions["Amount"].sum()

        ]

    }

)

# ------------------------------------------------------------
# MONTHLY INVESTMENT CHART
# ------------------------------------------------------------

monthly_investment_fig = px.bar(

    monthly_purchase,

    x="Month",

    y="Investment",

    title="Monthly Investment"

)

monthly_investment_fig.update_layout(

    template="plotly_white",

    title_x=0.5

)

# ------------------------------------------------------------
# MONTHLY REDEMPTION CHART
# ------------------------------------------------------------

monthly_redemption_fig = px.bar(

    monthly_redemption,

    x="Month",

    y="Redemption",

    title="Monthly Redemption"

)

monthly_redemption_fig.update_layout(

    template="plotly_white",

    title_x=0.5

)

# ------------------------------------------------------------
# NET INVESTMENT CHART
# ------------------------------------------------------------

cashflow_fig = px.line(

    cashflow,

    x="Month",

    y="Net Investment",

    markers=True,

    title="Net Monthly Investment"

)

cashflow_fig.update_layout(

    template="plotly_white",

    title_x=0.5

)

# ------------------------------------------------------------
# PORTFOLIO GROWTH CHART
# ------------------------------------------------------------

portfolio_growth_fig = px.line(
    portfolio_growth,
    x="Month",
    y="Amount Invested",
    markers=False,
    title="Portfolio Growth"

)

portfolio_growth_fig.update_layout(
    template="plotly_white",
    title_x=0.5,
    yaxis_title="Invested Amount",
    xaxis_title="Month",
    hovermode="x unified"

)


# ------------------------------------------------------------
# SIP VS LUMPSUM CHART
# ------------------------------------------------------------

sip_fig = px.pie(

    sip_summary,

    names="Category",

    values="Amount",

    hole=0.45,

    title="SIP vs Lumpsum"

)

sip_fig.update_layout(

    template="plotly_white",

    title_x=0.5

)

print()

print("=" * 60)

print("STEP 6C COMPLETED")

print("=" * 60)

# ============================================================
# PREMIUM DASHBOARD LAYOUT
# ============================================================

app.layout = html.Div(
    [

        # ====================================================
        # HEADER
        # ====================================================

        html.Div(
            [

                html.Div(
                    [
                        html.Div(
                            "₹",
                            style={
                                "width": "44px",
                                "height": "44px",
                                "borderRadius": "12px",
                                "backgroundColor": BLUE,
                                "color": "white",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                                "fontSize": "22px",
                                "fontWeight": "800",
                                "boxShadow": "0 6px 15px rgba(79,70,229,0.25)"
                            }
                        ),

                        html.Div(
                            [
                                html.Div(
                                    "MUTUAL FUND",
                                    style={
                                        "fontSize": "12px",
                                        "fontWeight": "700",
                                        "letterSpacing": "2px",
                                        "color": BLUE
                                    }
                                ),

                                html.Div(
                                    "Portfolio Dashboard",
                                    style={
                                        "fontSize": "25px",
                                        "fontWeight": "800",
                                        "color": TEXT,
                                        "letterSpacing": "-0.7px",
                                        "lineHeight": "1.1"
                                    }
                                )
                            ],
                            style={
                                "marginLeft": "12px"
                            }
                        )
                    ],

                    style={
                        "display": "flex",
                        "alignItems": "center"
                    }
                ),

                html.Div(
                    [
                        html.Div(
                            "PORTFOLIO SNAPSHOT",
                            style={
                                "fontSize": "10px",
                                "fontWeight": "700",
                                "letterSpacing": "1px",
                                "color": MUTED,
                                "textAlign": "right"
                            }
                        ),

                        html.Div(
                            today.strftime("%d %b %Y"),
                            style={
                                "fontSize": "13px",
                                "fontWeight": "600",
                                "color": TEXT,
                                "marginTop": "3px"
                            }
                        )
                    ]
                )

            ],

            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "backgroundColor": CARD,
                "borderBottom": f"1px solid {BORDER}",
                "padding": "22px 4px",
                "marginBottom": "22px"
            }
        ),


        # ====================================================
        # KPI CARDS
        # ====================================================

        html.Div(
            [

                kpi_card(
                    "Current Portfolio Value",
                    money(total_current),
                    "Current market value",
                    BLUE,
                    "₹"
                ),

                kpi_card(
                    "Total Invested",
                    money(total_invested),
                    "Gross purchases",
                    PURPLE,
                    "↗"
                ),

                kpi_card(
                    "Total Redeemed",
                    money(total_redeemed),
                    "Cash received",
                    ORANGE,
                    "↙"
                ),

                kpi_card(
                    "Absolute Return",
                    pct(total_return),
                    "Return on net capital",
                    GREEN,
                    "%"
                ),

                kpi_card(
                    "Portfolio XIRR",
                    pct(portfolio_xirr_display),
                    "Money-weighted annual return",
                    TEAL,
                    "★"
                ),

                kpi_card(
                    "Funds",
                    f"{fund_count}",
                    "Active portfolio funds",
                    BLUE,
                    "◉"
                )

            ],

            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(6, minmax(150px, 1fr))",
                "gap": "14px",
                "marginBottom": "24px"
            }
        ),


        # ====================================================
        # TABS
        # ====================================================

        dcc.Tabs(

            [

                # ==================================================
                # OVERVIEW
                # ==================================================

                dcc.Tab(

                    label="Overview",

                    children=[

                        html.Div(
                            [

                                html.Div(
                                    [
                                        dcc.Graph(
                                            figure=asset_fig,
                                            config={
                                                "displayModeBar": False,
                                                "responsive": True
                                            }
                                        )
                                    ],
                                    style={
                                        **SECTION_STYLE
                                    }
                                ),

                                html.Div(
                                    [
                                        dcc.Graph(
                                            figure=marketcap_fig,
                                            config={
                                                "displayModeBar": False,
                                                "responsive": True
                                            }
                                        )
                                    ],
                                    style={
                                        **SECTION_STYLE
                                    }
                                )

                            ],

                            style={
                                "display": "grid",
                                "gridTemplateColumns": "1fr 1fr",
                                "gap": "18px",
                                "marginBottom": "18px"
                            }
                        ),

                        html.Div(
                            [

                                html.Div(
                                    [
                                        dcc.Graph(
                                            figure=performer_fig,
                                            config={
                                                "displayModeBar": False,
                                                "responsive": True
                                            }
                                        )
                                    ],
                                    style={
                                        **SECTION_STYLE
                                    }
                                ),

                                html.Div(
                                    [
                                        dcc.Graph(
                                            figure=bottom_fig,
                                            config={
                                                "displayModeBar": False,
                                                "responsive": True
                                            }
                                        )
                                    ],
                                    style={
                                        **SECTION_STYLE
                                    }
                                )

                            ],

                            style={
                                "display": "grid",
                                "gridTemplateColumns": "1fr 1fr",
                                "gap": "18px"
                            }
                        )

                    ],

                    style={
                        "backgroundColor": "#F8FAFC",
                        "border": "none",
                        "padding": "16px 20px",
                        "fontWeight": "600",
                        "color": MUTED
                    },

                    selected_style={
                        "backgroundColor": CARD,
                        "border": "none",
                        "borderTop": f"3px solid {BLUE}",
                        "padding": "16px 20px",
                        "fontWeight": "700",
                        "color": BLUE
                    }
                ),


                # ==================================================
                # HOLDINGS
                # ==================================================

                dcc.Tab(

                    label="Holdings",

                    children=[

                        html.Div(
                            [

                                html.Div(
                                    [

                                        html.Div(
                                            [
                                                html.Div(
                                                    "Current Holdings",
                                                    style={
                                                        "fontSize": "19px",
                                                        "fontWeight": "750",
                                                        "color": TEXT
                                                    }
                                                ),

                                                html.Div(
                                                    f"{fund_count} funds • sorted by current value",
                                                    style={
                                                        "fontSize": "11px",
                                                        "color": MUTED,
                                                        "marginTop": "4px"
                                                    }
                                                )
                                            ]
                                        ),

                                        html.Div(
                                            "LIVE PORTFOLIO",
                                            style={
                                                "fontSize": "10px",
                                                "fontWeight": "700",
                                                "letterSpacing": "1px",
                                                "color": GREEN,
                                                "backgroundColor": GREEN_LIGHT,
                                                "padding": "7px 10px",
                                                "borderRadius": "20px"
                                            }
                                        )

                                    ],

                                    style={
                                        "display": "flex",
                                        "justifyContent": "space-between",
                                        "alignItems": "center",
                                        "marginBottom": "18px"
                                    }
                                ),

                                holdings_table

                            ],

                            style={
                                **SECTION_STYLE,
                                "padding": "20px 22px 22px 22px",
                                "width": "100%",
                                "boxSizing": "border-box"
                            }
                        )

                    ],

                    style={
                        "backgroundColor": "#F8FAFC",
                        "border": "none",
                        "padding": "16px 20px",
                        "fontWeight": "600",
                        "color": MUTED
                    },

                    selected_style={
                        "backgroundColor": CARD,
                        "border": "none",
                        "borderTop": f"3px solid {BLUE}",
                        "padding": "16px 20px",
                        "fontWeight": "700",
                        "color": BLUE
                    }
                ),


                # ==================================================
                # PERFORMANCE
                # ==================================================

                dcc.Tab(

                    label="Performance",

                    children=[

                        html.Div(
                            [

                                html.Div(
                                    [
                                        dcc.Graph(
                                            figure=portfolio_growth_fig,
                                            config={
                                                "displayModeBar": False,
                                                "responsive": True
                                            }
                                        )
                                    ],
                                    style={
                                        **SECTION_STYLE
                                    }
                                ),

                                html.Div(
                                    [

                                        html.Div(
                                            [
                                                dcc.Graph(
                                                    figure=purchase_fig,
                                                    config={
                                                        "displayModeBar": False,
                                                        "responsive": True
                                                    }
                                                )
                                            ],
                                            style={
                                                **SECTION_STYLE
                                            }
                                        ),

                                        html.Div(
                                            [
                                                dcc.Graph(
                                                    figure=redemption_fig,
                                                    config={
                                                        "displayModeBar": False,
                                                        "responsive": True
                                                    }
                                                )
                                            ],
                                            style={
                                                **SECTION_STYLE
                                            }
                                        )

                                    ],

                                    style={
                                        "display": "grid",
                                        "gridTemplateColumns": "1fr 1fr",
                                        "gap": "18px"
                                    }
                                )

                            ],

                            style={
                                "display": "flex",
                                "flexDirection": "column",
                                "gap": "18px"
                            }
                        )

                    ],

                    style={
                        "backgroundColor": "#F8FAFC",
                        "border": "none",
                        "padding": "16px 20px",
                        "fontWeight": "600",
                        "color": MUTED
                    },

                    selected_style={
                        "backgroundColor": CARD,
                        "border": "none",
                        "borderTop": f"3px solid {BLUE}",
                        "padding": "16px 20px",
                        "fontWeight": "700",
                        "color": BLUE
                    }
                ),


                # ==================================================
                # FUND HEALTH
                # ==================================================

                dcc.Tab(

                    label="Fund Health",

                    children=[

                        html.Div(
                            [

                                html.Div(
                                    [

                                        html.Div(
                                            [
                                                html.Div(
                                                    "Fund Health",
                                                    style={
                                                        "fontSize": "19px",
                                                        "fontWeight": "750",
                                                        "color": TEXT
                                                    }
                                                ),

                                                html.Div(
                                                    "XIRR-based portfolio health assessment",
                                                    style={
                                                        "fontSize": "11px",
                                                        "color": MUTED,
                                                        "marginTop": "4px"
                                                    }
                                                )
                                            ]
                                        ),

                                        html.Div(
                                            [
                                                html.Span(
                                                    "●",
                                                    style={
                                                        "color": GREEN,
                                                        "marginRight": "6px"
                                                    }
                                                ),
                                                "LIVE"
                                            ],
                                            style={
                                                "fontSize": "10px",
                                                "fontWeight": "700",
                                                "letterSpacing": "1px",
                                                "color": MUTED
                                            }
                                        )

                                    ],

                                    style={
                                        "display": "flex",
                                        "justifyContent": "space-between",
                                        "alignItems": "center",
                                        "marginBottom": "18px"
                                    }
                                ),

                                dash_table.DataTable(

                                    data=(

                                        dashboard

                                        .assign(

                                            Health=np.select(
                                                [
                                                    dashboard["XIRR %"] >= 15,
                                                    dashboard["XIRR %"] >= 10,
                                                    dashboard["XIRR %"] >= 5
                                                ],
                                                [
                                                    "🟢 HEALTHY",
                                                    "🔵 GOOD",
                                                    "🟡 REVIEW"
                                                ],
                                                default="🔴 WEAK"
                                            ),

                                            Action=np.select(
                                                [
                                                    dashboard["XIRR %"] >= 15,
                                                    dashboard["XIRR %"] >= 10,
                                                    dashboard["XIRR %"] >= 5
                                                ],
                                                [
                                                    "KEEP",
                                                    "KEEP / MONITOR",
                                                    "REVIEW"
                                                ],
                                                default="CONSIDER REPLACEMENT"
                                            ),

                                            Reason=np.select(
                                                [
                                                    dashboard["XIRR %"] >= 15,
                                                    dashboard["XIRR %"] >= 10,
                                                    dashboard["XIRR %"] >= 5
                                                ],
                                                [
                                                    "Strong XIRR",
                                                    "Good XIRR; continue monitoring",
                                                    "Moderate XIRR; compare with category peers"
                                                ],
                                                default="Low XIRR; review against alternatives"
                                            )

                                        )

                                        [
                                            [
                                                "Scheme Name",
                                                "Current Value",
                                                "Holding Weight %",
                                                "XIRR %",
                                                "Return %",
                                                "Asset Class",
                                                "Market Cap",
                                                "Health",
                                                "Action",
                                                "Reason"
                                            ]
                                        ]

                                        .sort_values(
                                            "XIRR %",
                                            ascending=False
                                        )

                                        .round(2)

                                        .to_dict("records")

                                    ),

                                    columns=[

                                        {
                                            "name": "Scheme Name",
                                            "id": "Scheme Name"
                                        },

                                        {
                                            "name": "Current Value",
                                            "id": "Current Value",
                                            "type": "numeric",
                                            "format": Format(
                                                precision=0,
                                                scheme=Scheme.fixed
                                            )
                                        },

                                        {
                                            "name": "Weight %",
                                            "id": "Holding Weight %",
                                            "type": "numeric",
                                            "format": Format(
                                                precision=2,
                                                scheme=Scheme.fixed
                                            )
                                        },

                                        {
                                            "name": "XIRR %",
                                            "id": "XIRR %",
                                            "type": "numeric",
                                            "format": Format(
                                                precision=2,
                                                scheme=Scheme.fixed
                                            )
                                        },

                                        {
                                            "name": "Return %",
                                            "id": "Return %",
                                            "type": "numeric",
                                            "format": Format(
                                                precision=2,
                                                scheme=Scheme.fixed
                                            )
                                        },

                                        {
                                            "name": "Asset Class",
                                            "id": "Asset Class"
                                        },

                                        {
                                            "name": "Market Cap",
                                            "id": "Market Cap"
                                        },

                                        {
                                            "name": "Health",
                                            "id": "Health"
                                        },

                                        {
                                            "name": "Action",
                                            "id": "Action"
                                        },

                                        {
                                            "name": "Reason",
                                            "id": "Reason"
                                        }

                                    ],

                                    sort_action="native",
                                    filter_action="native",
                                    page_action="native",
                                    page_size=20,

                                    style_table={
                                        "overflowX": "auto",
                                        "borderRadius": "12px",
                                        "border": f"1px solid {BORDER}",
                                        "backgroundColor": CARD
                                    },

                                    style_header={
                                        "backgroundColor": NAVY,
                                        "color": "white",
                                        "fontWeight": "700",
                                        "fontSize": "10px",
                                        "letterSpacing": "0.5px",
                                        "textTransform": "uppercase",
                                        "textAlign": "center",
                                        "padding": "14px 10px",
                                        "border": "none"
                                    },

                                    style_cell={
                                        "padding": "13px 10px",
                                        "fontSize": "12px",
                                        "fontFamily": "Inter, Segoe UI, Arial",
                                        "color": TEXT,
                                        "backgroundColor": CARD,
                                        "border": f"1px solid {BORDER}",
                                        "textAlign": "right",
                                        "height": "42px"
                                    },

                                    style_cell_conditional=[
                                        {
                                            "if": {
                                                "column_id": "Scheme Name"
                                            },
                                            "textAlign": "left",
                                            
                                            "minWidth": "360px"
                                            
                                            
                                        },

                                        {
                                            "if": {
                                                "column_id": "Health"
                                            },
                                            "textAlign": "center",
                                            "fontWeight": "700"
                                        },

                                        {
                                            "if": {
                                                "column_id": "Action"
                                            },
                                            "textAlign": "center",
                                            "fontWeight": "700"
                                        },

                                        {
                                            "if": {
                                                "column_id": "XIRR %"
                                            },
                                            "fontWeight": "700"
                                        }
                                    ],

                                    style_data_conditional=[

                                        {
                                            "if": {
                                                "row_index": "odd"
                                            },
                                            "backgroundColor": "#FAFBFD"
                                        },

                                        {
                                            "if": {
                                                "filter_query": "{XIRR %} >= 15",
                                                "column_id": "XIRR %"
                                            },
                                            "color": GREEN,
                                            "fontWeight": "700",
                                            "backgroundColor": GREEN_LIGHT
                                        },

                                        {
                                            "if": {
                                                "filter_query": "{XIRR %} >= 10 && {XIRR %} < 15",
                                                "column_id": "XIRR %"
                                            },
                                            "color": BLUE,
                                            "fontWeight": "700",
                                            "backgroundColor": BLUE_LIGHT
                                        },

                                        {
                                            "if": {
                                                "filter_query": "{XIRR %} >= 5 && {XIRR %} < 10",
                                                "column_id": "XIRR %"
                                            },
                                            "color": ORANGE,
                                            "fontWeight": "700",
                                            "backgroundColor": ORANGE_LIGHT
                                        },

                                        {
                                            "if": {
                                                "filter_query": "{XIRR %} < 5",
                                                "column_id": "XIRR %"
                                            },
                                            "color": RED,
                                            "fontWeight": "700",
                                            "backgroundColor": RED_LIGHT
                                        },

                                        {
                                            "if": {
                                                "filter_query": "{Action} = 'KEEP'",
                                                "column_id": "Action"
                                            },
                                            "color": GREEN,
                                            "fontWeight": "700"
                                        },

                                        {
                                            "if": {
                                                "filter_query": "{Action} = 'REVIEW'",
                                                "column_id": "Action"
                                            },
                                            "color": ORANGE,
                                            "fontWeight": "700"
                                        },

                                        {
                                            "if": {
                                                "filter_query": "{Action} = 'CONSIDER REPLACEMENT'",
                                                "column_id": "Action"
                                            },
                                            "color": RED,
                                            "fontWeight": "700"
                                        }
                                    ],

                                    style_filter={
                                        "backgroundColor": "#F8FAFC",
                                        "color": TEXT,
                                        "fontSize": "10px"
                                    }

                                )

                            ],

                            style={
                                **SECTION_STYLE,
                                "padding": "22px"
                            }
                        )

                    ],

                    style={
                        "backgroundColor": "#F8FAFC",
                        "border": "none",
                        "padding": "16px 20px",
                        "fontWeight": "600",
                        "color": MUTED
                    },

                    selected_style={
                        "backgroundColor": CARD,
                        "border": "none",
                        "borderTop": f"3px solid {BLUE}",
                        "padding": "16px 20px",
                        "fontWeight": "700",
                        "color": BLUE
                    }
                )

            ],

            colors={
                "border": BORDER,
                "primary": BLUE,
                "background": BG
            },

            style={
                "fontFamily": "Inter, Segoe UI, Arial",
                "fontSize": "13px",
                "backgroundColor": BG
            }

        )

    ],

    style=PAGE_STYLE
)
    
# ------------------------------------------------------------
# EXPORT
# ------------------------------------------------------------

asset_summary.to_csv(

    "asset_summary.csv",

    index=False

)

marketcap_summary.to_csv(

    "marketcap_summary.csv",

    index=False

)

amc_summary.to_csv(

    "amc_summary.csv",

    index=False

)

print()

print("="*60)

print("STEP 6A COMPLETED")

print("="*60)





# ------------------------------------------------------------
# AMC ALLOCATION
# ------------------------------------------------------------

amc_fig = px.bar(

    amc_summary.sort_values(

        "Current Value",

        ascending=False

    ),

    x="AMC",

    y="Current Value",

    title="AMC Exposure"

)

amc_fig.update_layout(

    title_x=0.5,

    template="plotly_white"

)

# ------------------------------------------------------------
# TOP 10 HOLDINGS
# ------------------------------------------------------------

top10 = (

    dashboard

    .sort_values(

        "Current Value",

        ascending=False

    )

    .head(10)

)

top10_fig = px.bar(

    top10,

    x="Scheme Name",

    y="Current Value",

    title="Top 10 Holdings"

)

top10_fig.update_layout(

    title_x=0.5,

    xaxis_tickangle=-45,

    template="plotly_white"

)

# ------------------------------------------------------------
# BEST PERFORMERS
# ------------------------------------------------------------

best5 = (

    dashboard

    .sort_values(

        "XIRR %",

        ascending=False

    )

    .head(5)

)

best5_fig = px.bar(

    best5,

    x="Scheme Name",

    y="XIRR %",

    title="Top 5 Performers"

)

best5_fig.update_layout(

    title_x=0.5,

    xaxis_tickangle=-45,

    template="plotly_white"

)

# ------------------------------------------------------------
# WORST PERFORMERS
# ------------------------------------------------------------

worst5 = (

    dashboard

    .sort_values(

        "XIRR %",

        ascending=True

    )

    .head(5)

)

worst5_fig = px.bar(

    worst5,

    x="Scheme Name",

    y="XIRR %",

    title="Bottom 5 Performers"

)

worst5_fig.update_layout(

    title_x=0.5,

    xaxis_tickangle=-45,

    template="plotly_white"

)

print()

print("=" * 60)

print("STEP 6B COMPLETED")

print("=" * 60)



# ============================================================
# STEP 6D - ADVANCED FUND ANALYTICS
# (Place AFTER Step 6C and BEFORE Step 5B)
# ============================================================

# ------------------------------------------------------------
# TOP PROFIT CONTRIBUTORS
# ------------------------------------------------------------

top_profit = (

    dashboard

    .sort_values(

        "Profit",

        ascending=False

    )

    .head(10)

)

# ------------------------------------------------------------
# TOP LOSS CONTRIBUTORS
# ------------------------------------------------------------

top_loss = (

    dashboard

    .sort_values(

        "Profit",

        ascending=True

    )

    .head(10)

)

# ------------------------------------------------------------
# TOP XIRR
# ------------------------------------------------------------

top_xirr = (

    dashboard

    .sort_values(

        "XIRR %",

        ascending=False

    )

    .head(10)

)

# ------------------------------------------------------------
# LOWEST XIRR
# ------------------------------------------------------------

bottom_xirr = (

    dashboard

    .sort_values(

        "XIRR %",

        ascending=True

    )

    .head(10)

)

# ------------------------------------------------------------
# PORTFOLIO CONCENTRATION
# ------------------------------------------------------------

portfolio_concentration = (

    dashboard

    [

        [

            "Scheme Name",

            "Current Value"

        ]

    ]

    .copy()

)

portfolio_concentration["Weight %"] = (

    portfolio_concentration["Current Value"]

    /

    portfolio_concentration["Current Value"].sum()

    *100

)

portfolio_concentration = (

    portfolio_concentration

    .sort_values(

        "Weight %",

        ascending=False

    )

)

# ------------------------------------------------------------
# PROFIT DISTRIBUTION
# ------------------------------------------------------------

profit_distribution_fig = px.histogram(

    dashboard,

    x="Profit",

    nbins=20,

    title="Profit Distribution"

)

profit_distribution_fig.update_layout(

    template="plotly_white",

    title_x=0.5

)

# ------------------------------------------------------------
# PORTFOLIO CONCENTRATION
# ------------------------------------------------------------

concentration_fig = px.treemap(

    portfolio_concentration,

    path=["Scheme Name"],

    values="Current Value",

    title="Portfolio Concentration"

)

concentration_fig.update_layout(

    template="plotly_white",

    title_x=0.5

)

# ------------------------------------------------------------
# TOP PROFIT CHART
# ------------------------------------------------------------

top_profit_fig = px.bar(

    top_profit,

    x="Scheme Name",

    y="Profit",

    title="Top Profit Contributors"

)

top_profit_fig.update_layout(

    template="plotly_white",

    title_x=0.5,

    xaxis_tickangle=-45

)

# ------------------------------------------------------------
# TOP LOSS CHART
# ------------------------------------------------------------

top_loss_fig = px.bar(

    top_loss,

    x="Scheme Name",

    y="Profit",

    title="Top Loss Contributors"

)

top_loss_fig.update_layout(

    template="plotly_white",

    title_x=0.5,

    xaxis_tickangle=-45

)

# ------------------------------------------------------------
# XIRR RANKING
# ------------------------------------------------------------

xirr_rank_fig = px.bar(

    top_xirr,

    x="Scheme Name",

    y="XIRR %",

    title="Highest XIRR"

)

xirr_rank_fig.update_layout(

    template="plotly_white",

    title_x=0.5,

    xaxis_tickangle=-45

)

# ------------------------------------------------------------
# LOWEST XIRR
# ------------------------------------------------------------

bottom_xirr_fig = px.bar(

    bottom_xirr,

    x="Scheme Name",

    y="XIRR %",

    title="Lowest XIRR"

)

bottom_xirr_fig.update_layout(

    template="plotly_white",

    title_x=0.5,

    xaxis_tickangle=-45

)

# ------------------------------------------------------------
# SUMMARY TABLE
# ------------------------------------------------------------

analytics_summary = pd.DataFrame(

    {

        "Metric":[

            "Total Funds",

            "Current Value",

            "Invested Amount",

            "Redeemed Amount",

            "Profit",

            "Absolute Return %",

            "Portfolio XIRR %"

        ],

        "Value":[

            len(dashboard),

            current_value,

            total_invested,

            total_redeemed,

            profit,

            profit,

            portfolio_xirr_value

        ]

    }

)

print()

print("=" * 60)

print("STEP 6D COMPLETED")

print("=" * 60)

# ============================================================
# STEP 6E - DASHBOARD ENHANCEMENTS
# (Place AFTER Step 6D and BEFORE Step 5B)
# ============================================================

# ------------------------------------------------------------
# PORTFOLIO HEALTH SCORE
# ------------------------------------------------------------

positive_funds = len(

    dashboard[dashboard["Profit"] > 0]

)

negative_funds = len(

    dashboard[dashboard["Profit"] <= 0]

)

health_score = (

    positive_funds

    /

    len(dashboard)

    *100

)

# ------------------------------------------------------------
# DIVERSIFICATION SCORE
# ------------------------------------------------------------

top5_weight = (

    dashboard

    .nlargest(

        5,

        "Current Value"

    )["Current Value"]

    .sum()

)

diversification_score = (

    100

    -

    (

        top5_weight

        /

        current_value

        *100

    )

)

# ------------------------------------------------------------
# KPI TABLE
# ------------------------------------------------------------

kpi_table = pd.DataFrame(

    {

        "KPI":[

            "Portfolio Health",

            "Diversification",

            "Positive Funds",

            "Negative Funds",

            "Total Holdings"

        ],

        "Value":[

            round(

                health_score,

                2

            ),

            round(

                diversification_score,

                2

            ),

            positive_funds,

            negative_funds,

            len(dashboard)

        ]

    }

)

# ------------------------------------------------------------
# PORTFOLIO WEIGHT
# ------------------------------------------------------------

dashboard["Portfolio Weight %"] = (

    dashboard["Current Value"]

    /

    dashboard["Current Value"].sum()

    *100

)

# ------------------------------------------------------------
# PROFIT %
# ------------------------------------------------------------

dashboard["Profit %"] = (

    dashboard["Profit"]

    /

    dashboard["Cost Value"]

    *100

)

dashboard["Profit %"] = (

    dashboard["Profit %"]

    .replace(

        [

            np.inf,

            -np.inf

        ],

        0

    )

    .fillna(

        0

    )

)

# ------------------------------------------------------------
# HOLDING RANK
# ------------------------------------------------------------

dashboard["Holding Rank"] = (

    dashboard["Current Value"]

    .rank(

        ascending=False,

        method="dense"

    )

)

# ------------------------------------------------------------
# RISK LABEL
# ------------------------------------------------------------

dashboard["Risk"] = np.where(

    dashboard["Market Cap"] == "Small Cap",

    "High",

    np.where(

        dashboard["Market Cap"] == "Mid Cap",

        "Moderate",

        np.where(

            dashboard["Market Cap"] == "Flexi Cap",

            "Moderate",

            np.where(

                dashboard["Asset Class"] == "Debt",

                "Low",

                "Medium"

            )

        )

    )

)

# ------------------------------------------------------------
# PROFIT LABEL
# ------------------------------------------------------------

dashboard["Performance"] = np.where(

    dashboard["Profit"] > 0,

    "Gain",

    "Loss"

)

# ------------------------------------------------------------
# PORTFOLIO WEIGHT CHART
# ------------------------------------------------------------

weight_fig = px.bar(

    dashboard

    .sort_values(

        "Portfolio Weight %",

        ascending=False

    ),

    x="Scheme Name",

    y="Portfolio Weight %",

    title="Portfolio Weight"

)

weight_fig.update_layout(

    template="plotly_white",

    title_x=0.5,

    xaxis_tickangle=-45

)

# ------------------------------------------------------------
# RISK DISTRIBUTION
# ------------------------------------------------------------

risk_fig = px.pie(

    dashboard,

    names="Risk",

    values="Current Value",

    hole=0.45,

    title="Risk Distribution"

)

risk_fig.update_layout(

    template="plotly_white",

    title_x=0.5

)

# ------------------------------------------------------------
# PERFORMANCE DISTRIBUTION
# ------------------------------------------------------------

performance_fig = px.pie(

    dashboard,

    names="Performance",

    values="Current Value",

    hole=0.45,

    title="Gain vs Loss"

)

performance_fig.update_layout(

    template="plotly_white",

    title_x=0.5

)

# ------------------------------------------------------------
# KPI PRINT
# ------------------------------------------------------------

print()

print("=" * 60)

print("PORTFOLIO HEALTH")

print("=" * 60)

print(kpi_table)

print()

print("=" * 60)

print("STEP 6E COMPLETED")

print("=" * 60)

# ============================================================
# STEP 6F - EXPORT REPORTS
# (Place AFTER Step 6E and BEFORE Step 5B)
# ============================================================

import os

EXPORT_FOLDER = "MF_Dashboard_Reports"

os.makedirs(EXPORT_FOLDER, exist_ok=True)

# ------------------------------------------------------------
# EXPORT DASHBOARD
# ------------------------------------------------------------

dashboard.to_csv(

    os.path.join(

        EXPORT_FOLDER,

        "Dashboard.csv"

    ),

    index=False

)

# ------------------------------------------------------------
# EXPORT SUMMARY
# ------------------------------------------------------------

analytics_summary.to_csv(

    os.path.join(

        EXPORT_FOLDER,

        "Portfolio_Summary.csv"

    ),

    index=False

)

# ------------------------------------------------------------
# EXPORT KPI
# ------------------------------------------------------------

kpi_table.to_csv(

    os.path.join(

        EXPORT_FOLDER,

        "KPI_Table.csv"

    ),

    index=False

)

# ------------------------------------------------------------
# EXPORT ASSET SPLIT
# ------------------------------------------------------------

asset_summary.to_csv(

    os.path.join(

        EXPORT_FOLDER,

        "Asset_Allocation.csv"

    ),

    index=False

)

# ------------------------------------------------------------
# EXPORT MARKET CAP
# ------------------------------------------------------------

marketcap_summary.to_csv(

    os.path.join(

        EXPORT_FOLDER,

        "Market_Cap_Allocation.csv"

    ),

    index=False

)

# ------------------------------------------------------------
# EXPORT AMC
# ------------------------------------------------------------

amc_summary.to_csv(

    os.path.join(

        EXPORT_FOLDER,

        "AMC_Allocation.csv"

    ),

    index=False

)

# ------------------------------------------------------------
# EXPORT CASHFLOW
# ------------------------------------------------------------

cashflow.to_csv(

    os.path.join(

        EXPORT_FOLDER,

        "Cashflow.csv"

    ),

    index=False

)

# ------------------------------------------------------------
# EXPORT MONTHLY PURCHASE
# ------------------------------------------------------------

monthly_purchase.to_csv(

    os.path.join(

        EXPORT_FOLDER,

        "Monthly_Investment.csv"

    ),

    index=False

)

# ------------------------------------------------------------
# EXPORT MONTHLY REDEMPTION
# ------------------------------------------------------------

monthly_redemption.to_csv(

    os.path.join(

        EXPORT_FOLDER,

        "Monthly_Redemption.csv"

    ),

    index=False

)

# ------------------------------------------------------------
# EXPORT PORTFOLIO GROWTH
# ------------------------------------------------------------

portfolio_growth.to_csv(

    os.path.join(

        EXPORT_FOLDER,

        "Portfolio_Growth.csv"

    ),

    index=False

)

# ------------------------------------------------------------
# EXPORT SIP ANALYSIS
# ------------------------------------------------------------

sip_summary.to_csv(

    os.path.join(

        EXPORT_FOLDER,

        "SIP_vs_Lumpsum.csv"

    ),

    index=False

)

# ------------------------------------------------------------
# EXPORT TOP / BOTTOM
# ------------------------------------------------------------

top_profit.to_csv(

    os.path.join(

        EXPORT_FOLDER,

        "Top_Profit.csv"

    ),

    index=False

)

top_loss.to_csv(

    os.path.join(

        EXPORT_FOLDER,

        "Top_Loss.csv"

    ),

    index=False

)

top_xirr.to_csv(

    os.path.join(

        EXPORT_FOLDER,

        "Top_XIRR.csv"

    ),

    index=False

)

bottom_xirr.to_csv(

    os.path.join(

        EXPORT_FOLDER,

        "Bottom_XIRR.csv"

    ),

    index=False

)

# ------------------------------------------------------------
# EXPORT EXCEL
# ------------------------------------------------------------

with pd.ExcelWriter(

    os.path.join(

        EXPORT_FOLDER,

        "MF_Dashboard_Report.xlsx"

    ),

    engine="openpyxl"

) as writer:

    dashboard.to_excel(

        writer,

        sheet_name="Dashboard",

        index=False

    )

    analytics_summary.to_excel(

        writer,

        sheet_name="Summary",

        index=False

    )

    kpi_table.to_excel(

        writer,

        sheet_name="KPI",

        index=False

    )

    asset_summary.to_excel(

        writer,

        sheet_name="Asset Allocation",

        index=False

    )

    marketcap_summary.to_excel(

        writer,

        sheet_name="Market Cap",

        index=False

    )

    amc_summary.to_excel(

        writer,

        sheet_name="AMC",

        index=False

    )

    cashflow.to_excel(

        writer,

        sheet_name="Cashflow",

        index=False

    )

    monthly_purchase.to_excel(

        writer,

        sheet_name="Monthly Investment",

        index=False

    )

    monthly_redemption.to_excel(

        writer,

        sheet_name="Monthly Redemption",

        index=False

    )

    portfolio_growth.to_excel(

        writer,

        sheet_name="Portfolio Growth",

        index=False

    )

    sip_summary.to_excel(

        writer,

        sheet_name="SIP Analysis",

        index=False

    )

print()

print("=" * 60)

print("STEP 6F COMPLETED")

print("REPORTS EXPORTED TO:", EXPORT_FOLDER)

print("=" * 60)

# ============================================================
# STEP 7 - FINAL CLEANUP
# (Place AFTER Step 6F and BEFORE Step 5B)
# ============================================================

# ------------------------------------------------------------
# ROUND NUMBERS
# ------------------------------------------------------------

numeric_cols = dashboard.select_dtypes(include="number").columns

dashboard[numeric_cols] = dashboard[numeric_cols].round(2)

asset_summary = asset_summary.round(2)

marketcap_summary = marketcap_summary.round(2)

amc_summary = amc_summary.round(2)

analytics_summary = analytics_summary.round(2)

cashflow = cashflow.round({"Investment":2,"Redemption":2,"Net Investment":2})

monthly_purchase = monthly_purchase.round({"Investment":2})

monthly_redemption = monthly_redemption.round({"Redemption":2})

portfolio_growth = portfolio_growth.round({"Amount Invested":2})

sip_summary = sip_summary.round(2)

kpi_table = kpi_table.round(2)

# ------------------------------------------------------------
# SORT HOLDINGS
# ------------------------------------------------------------

dashboard = (

    dashboard

    .sort_values(

        "Current Value",

        ascending=False

    )

    .reset_index(

        drop=True

    )

)

dashboard["Holding Rank"] = range(

    1,

    len(dashboard)+1

)

# ------------------------------------------------------------
# FORMAT DASHBOARD
# ------------------------------------------------------------

dashboard["Invested Amount"] = dashboard["Cost Value"].astype(float)

dashboard["Current Value"] = dashboard["Current Value"].astype(float)

dashboard["Profit"] = dashboard["Profit"].astype(float)

dashboard["Return %"] = dashboard["Return %"].astype(float)

dashboard["XIRR %"] = dashboard["XIRR %"].astype(float)

dashboard["Portfolio Weight %"] = dashboard["Portfolio Weight %"].astype(float)

# ------------------------------------------------------------
# FINAL EXPORT
# ------------------------------------------------------------

dashboard.to_csv(

    "dashboard_final.csv",

    index=False

)

# ------------------------------------------------------------
# FINAL SUMMARY
# ------------------------------------------------------------

print()

print("="*70)

print("MUTUAL FUND DASHBOARD READY")

print("="*70)

print()

print("Funds                :",len(dashboard))

print("Current Value        :",round(current_value,2))

print("Invested Amount      :",round(total_invested,2))

print("Redeemed Amount      :",round(total_redeemed,2))

print("Profit               :",round(profit,2))

print("Return %             :", round((profit / total_invested) * 100, 2))

print("Portfolio XIRR %     :",round(portfolio_xirr_value,2))

print()

print("="*70)

print("ALL MODULES LOADED SUCCESSFULLY")

print("="*70)

print()

print("Step 1  ✓")

print("Step 2  ✓")

print("Step 3  ✓")

print("Step 4  ✓")

print("Step 5A ✓")

print("Step 6A ✓")

print("Step 6B ✓")

print("Step 6C ✓")

print("Step 6D ✓")

print("Step 6E ✓")

print("Step 6F ✓")

print("Step 7  ✓")

print()

print("="*70)

print("STARTING DASHBOARD...")

print("="*70)

# ============================================================
# STEP 5B - DASHBOARD CALLBACKS
# ============================================================

from dash.dependencies import Input, Output

# ------------------------------------------------------------
# HOLDINGS TABLE - FORMAT VALUES
# ------------------------------------------------------------

@app.callback(
    Output("holdings-table", "data"),
    Input("holdings-table", "page_current"),
    Input("holdings-table", "page_size"),
    Input("holdings-table", "filter_query"),
    Input("holdings-table", "sort_by")
)
def update_holdings_table(page_current, page_size, filter_query, sort_by):

    df = dash_portfolio.copy()

    # --------------------------------------------------------
    # FILTER
    # --------------------------------------------------------

    if filter_query:

        try:
            from dash.dash_table import filtering

            filtering_expression = filtering.split_filter_part(
                filter_query
            )

            if filtering_expression:

                col, operator, value = filtering_expression

                if operator == "=":
                    df = df[df[col].astype(str) == value]

                elif operator == "contains":
                    df = df[
                        df[col]
                        .astype(str)
                        .str.contains(
                            value,
                            case=False,
                            na=False
                        )
                    ]

        except Exception:
            pass

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    if sort_by:

        for sort in reversed(sort_by):

            column = sort["column_id"]
            direction = sort["direction"]

            if column in df.columns:

                df = df.sort_values(
                    column,
                    ascending=(direction == "asc")
                )

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    if page_current is None:
        page_current = 0

    if page_size is None:
        page_size = 15

    start = page_current * page_size
    end = start + page_size

    return df.iloc[start:end][table_columns].to_dict(
        "records"
    )


# ------------------------------------------------------------
# PRINT STATUS
# ------------------------------------------------------------

print("=" * 60)
print("STEP 5B LOADED")
print("=" * 60)


# ------------------------------------------------------------
# OPEN DASHBOARD AUTOMATICALLY
# ------------------------------------------------------------

def open_dashboard():

    webbrowser.open_new(
        "http://127.0.0.1:8050/"
    )

# ------------------------------------------------------------
# RUN DASH
# ------------------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=False,
        port=8050
    )




