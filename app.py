import time

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="GridGuard | Energy Theft Intelligence",
    page_icon="⚡",
    layout="wide",
)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

    :root {
        --panel: #ffffff;
        --ink: #13233a;
    }

    html, body, [class*="css"] {
        font-family: "Space Grotesk", "Segoe UI", sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 15% 20%, #e9f4ff 0%, #f4f7fb 35%, #f6fbff 100%);
        color: #12263f;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #101b30 0%, #1b2d4e 70%, #20355e 100%);
    }

    section[data-testid="stSidebar"] * {
        color: #f2f5fb !important;
    }

    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.4rem;
    }

    .hero {
        background: linear-gradient(120deg, #0b3a75 0%, #0a84ff 55%, #12b886 100%);
        padding: 1.35rem 1.6rem;
        border-radius: 16px;
        color: #ffffff;
        box-shadow: 0 10px 28px rgba(15, 45, 90, 0.22);
        margin-bottom: 0.9rem;
    }

    .hero h1 {
        margin: 0;
        font-size: 1.45rem;
        font-weight: 700;
    }

    .hero p {
        margin: 0.35rem 0 0;
        opacity: 0.95;
        font-size: 0.92rem;
    }

    .section-title {
        font-size: 1.02rem;
        font-weight: 700;
        color: #0f2744 !important;
        margin: 0.8rem 0 0.35rem;
    }

    div[data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid #dce6f5;
        padding: 0.7rem 0.85rem;
        border-radius: 12px;
        box-shadow: 0 4px 14px rgba(15, 45, 90, 0.08);
    }

    [data-testid="stMetricLabel"] {
        color: #51627a !important;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: #0f2744 !important;
        font-weight: 700;
    }

    [data-testid="stMetricDelta"] {
        font-weight: 600;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.4rem;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        background: rgba(255,255,255,0.74);
        border: 1px solid #dce6f5;
        padding: 0.35rem 0.8rem;
    }

    .stTabs [aria-selected="true"] {
        background: #0a84ff !important;
        color: #ffffff !important;
        border-color: #0a84ff !important;
    }

    .status-pill {
        display: inline-block;
        padding: 0.3rem 0.6rem;
        border-radius: 999px;
        font-weight: 600;
        font-size: 0.78rem;
        margin-top: 0.2rem;
    }

    .status-normal {
        color: #0d6e4b;
        background: #d3f9d8;
        border: 1px solid #8ce99a;
    }

    .status-risk {
        color: #c92a2a;
        background: #ffe3e3;
        border: 1px solid #ffa8a8;
    }

    .meta-row {
        margin-top: 0.55rem;
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }

    .meta-badge {
        background: rgba(255,255,255,0.18);
        color: #ffffff;
        border: 1px solid rgba(255,255,255,0.35);
        border-radius: 999px;
        padding: 0.22rem 0.6rem;
        font-size: 0.76rem;
    }

    .glass-card {
        background: rgba(255,255,255,0.78);
        border: 1px solid #dce6f5;
        border-radius: 14px;
        padding: 0.85rem;
        box-shadow: 0 8px 20px rgba(13, 52, 110, 0.08);
    }

    .insight-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.65rem;
        margin-bottom: 0.6rem;
    }

    .insight-card {
        background: rgba(255,255,255,0.85);
        border: 1px solid #dce6f5;
        border-radius: 12px;
        padding: 0.6rem 0.75rem;
    }

    .insight-card h4 {
        margin: 0;
        font-size: 0.75rem;
        color: #5e6f88;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }

    .insight-card p {
        margin: 0.2rem 0 0;
        font-size: 0.95rem;
        color: #10243d;
        font-weight: 600;
    }

    .chart-heading {
        background: linear-gradient(90deg, rgba(10,132,255,0.15), rgba(18,184,134,0.12));
        border: 1px solid #cfe2ff;
        border-radius: 12px;
        padding: 0.6rem 0.85rem;
        margin: 0.55rem 0;
        color: #0b3a75;
        font-weight: 700;
    }

    [data-testid="stCaptionContainer"] p {
        color: #334a66 !important;
        font-weight: 500;
    }

    .js-plotly-plot .plotly .gtitle,
    .js-plotly-plot .plotly .xtitle,
    .js-plotly-plot .plotly .ytitle,
    .js-plotly-plot .plotly .xtick text,
    .js-plotly-plot .plotly .ytick text,
    .js-plotly-plot .plotly .legendtext {
        fill: #1a2f47 !important;
        color: #1a2f47 !important;
        opacity: 1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> pd.DataFrame:
    data = pd.read_csv("Final_Model_Output.csv")
    data.columns = data.columns.str.strip().str.lower()

    datetime_col = next((c for c in data.columns if "date" in c or "time" in c), None)
    actual_col = next((c for c in data.columns if "actual" in c), None)
    pred_col = next((c for c in data.columns if "pred" in c), None)

    if not datetime_col or not actual_col or not pred_col:
        raise ValueError("Dataset must include datetime/time, actual, and predicted columns.")

    theft_candidates = [c for c in data.columns if "theft" in c or "flag" in c]
    theft_col = theft_candidates[0] if theft_candidates else data.columns[-1]

    data = data.rename(
        columns={
            datetime_col: "datetime",
            actual_col: "actual",
            pred_col: "predicted",
            theft_col: "theft",
        }
    )

    data["datetime"] = pd.to_datetime(data["datetime"], errors="coerce")
    data = data.dropna(subset=["datetime"]).copy()

    data["actual"] = pd.to_numeric(data["actual"], errors="coerce")
    data["predicted"] = pd.to_numeric(data["predicted"], errors="coerce")
    data["theft"] = pd.to_numeric(data["theft"], errors="coerce").fillna(0).astype(int)
    data = data.dropna(subset=["actual", "predicted"]).copy()

    meter_candidates = [c for c in data.columns if "meter" in c]
    if meter_candidates:
        data = data.rename(columns={meter_candidates[0]: "meter_id"})
        data["meter_id"] = data["meter_id"].astype(str)
    else:
        np.random.seed(42)
        data["meter_id"] = np.random.choice(
            ["Meter-1000", "Meter-1001", "Meter-1002", "Meter-1003"],
            size=len(data),
            p=[0.28, 0.26, 0.24, 0.22],
        )

    data = data.sort_values("datetime").reset_index(drop=True)
    return data


def enforce_plot_visibility(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        font=dict(color="#1a2f47", size=13),
        legend_font=dict(color="#1a2f47", size=12),
    )
    fig.update_xaxes(
        tickfont=dict(color="#1f2f46", size=12),
        title_font=dict(color="#1f2f46", size=14),
        gridcolor="#d8e2f0",
        automargin=True,
    )
    fig.update_yaxes(
        tickfont=dict(color="#1f2f46", size=12),
        title_font=dict(color="#1f2f46", size=14),
        gridcolor="#d8e2f0",
        automargin=True,
    )
    return fig


def build_figure(df: pd.DataFrame, title: str, is_live: bool = False) -> go.Figure:
    theft_points = df[df["theft"] == 1]
    latest_row = df.iloc[-1]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["predicted"],
            mode="lines",
            name="Predicted",
            line=dict(color="#1c7ed6", width=2.8, dash="dot"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["actual"],
            mode="lines",
            name="Actual",
            line=dict(color="#f08c00", width=3.2),
            fill="tozeroy" if is_live else None,
            fillcolor="rgba(240,140,0,0.12)" if is_live else None,
        )
    )

    if not theft_points.empty:
        fig.add_trace(
            go.Scatter(
                x=theft_points["datetime"],
                y=theft_points["actual"],
                mode="markers",
                name="Theft Flag",
                marker=dict(color="#e03131", size=11 if is_live else 9, symbol="diamond"),
            )
        )

    fig.add_trace(
        go.Scatter(
            x=[latest_row["datetime"]],
            y=[latest_row["actual"]],
            mode="markers+text",
            name="Latest",
            marker=dict(color="#0b3a75", size=12, line=dict(width=2, color="#ffffff")),
            text=["Now"],
            textposition="top center",
        )
    )

    fig.update_layout(
        template="plotly_white",
        title={
            "text": title,
            "font": {"size": 20 if is_live else 17, "color": "#0f2744"},
            "x": 0.01,
            "xanchor": "left",
        },
        height=500 if is_live else 480,
        margin=dict(l=20, r=20, t=58 if is_live else 50, b=20),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0.98)",
        font=dict(color="#10243d", size=13),
        xaxis_title="Timestamp",
        yaxis_title="Consumption (kWh)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0),
        hovermode="x unified",
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#d8e2f0",
        tickfont=dict(color="#1f2f46", size=12),
        title_font=dict(color="#1f2f46", size=14),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#d8e2f0",
        tickfont=dict(color="#1f2f46", size=12),
        title_font=dict(color="#1f2f46", size=14),
    )
    return enforce_plot_visibility(fig)


def risk_score(df: pd.DataFrame) -> float:
    theft_rate = float(df["theft"].mean()) if len(df) else 0.0
    deviation = np.abs(df["actual"] - df["predicted"])
    scale = float(df["actual"].mean() + 1e-6)
    rel_deviation = float(deviation.mean() / scale)
    raw = (0.65 * theft_rate + 0.35 * min(rel_deviation, 1.0)) * 100
    return round(min(raw, 100.0), 2)


def evaluate_model(df: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    eval_df = df.copy()
    eval_df["deviation_abs"] = np.abs(eval_df["actual"] - eval_df["predicted"])
    threshold = float(eval_df["deviation_abs"].quantile(0.85))
    eval_df["model_theft_pred"] = (eval_df["deviation_abs"] >= threshold).astype(int)

    y_true = eval_df["theft"].astype(int)
    y_pred = eval_df["model_theft_pred"].astype(int)

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    accuracy = (tp + tn) / max(len(eval_df), 1)

    metrics = {
        "threshold": threshold,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }
    return metrics, eval_df


def build_risk_gauge(score: float) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "%", "font": {"size": 30, "color": "#0b3a75"}},
            title={"text": "Risk Index", "font": {"size": 18}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#7c8ea8"},
                "bar": {"color": "#0a84ff", "thickness": 0.32},
                "steps": [
                    {"range": [0, 35], "color": "#d3f9d8"},
                    {"range": [35, 65], "color": "#fff3bf"},
                    {"range": [65, 100], "color": "#ffe3e3"},
                ],
                "threshold": {"line": {"color": "#e03131", "width": 3}, "value": 35},
            },
        )
    )
    fig.update_layout(
        height=280,
        margin=dict(l=15, r=15, t=30, b=10),
        paper_bgcolor="rgba(255,255,255,0)",
    )
    return enforce_plot_visibility(fig)


def build_fleet_ranking(df: pd.DataFrame) -> go.Figure:
    ranked = (
        df.groupby("meter_id", as_index=False)
        .agg(theft_cases=("theft", "sum"), total_records=("theft", "size"))
        .sort_values("theft_cases", ascending=False)
    )
    ranked["theft_rate"] = ranked["theft_cases"] / ranked["total_records"] * 100
    fig = go.Figure(
        go.Bar(
            x=ranked["meter_id"],
            y=ranked["theft_rate"],
            marker_color=["#e03131" if v >= 20 else "#1c7ed6" for v in ranked["theft_rate"]],
            text=[f"{v:.1f}%" for v in ranked["theft_rate"]],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Fleet Theft Rate Comparison",
        height=280,
        margin=dict(l=20, r=20, t=42, b=20),
        yaxis_title="Theft Rate (%)",
        xaxis_title="Meter",
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0.96)",
        font=dict(color="#10243d", size=13),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#e8eef7")
    return enforce_plot_visibility(fig)


def build_theft_timeline(df: pd.DataFrame) -> go.Figure:
    timeline = df.copy()
    timeline["day"] = timeline["datetime"].dt.date
    timeline = timeline.groupby("day", as_index=False).agg(theft_cases=("theft", "sum"))
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=timeline["day"],
            y=timeline["theft_cases"],
            marker_color="#e03131",
            name="Daily Theft Cases",
        )
    )
    fig.update_layout(
        title="Daily Theft Trend",
        height=320,
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis_title="Date",
        yaxis_title="No. of Theft Flags",
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0.96)",
        font=dict(color="#10243d", size=13),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#e8eef7")
    return enforce_plot_visibility(fig)


def build_hourly_profile(df: pd.DataFrame) -> go.Figure:
    hourly = df.copy()
    hourly["hour"] = hourly["datetime"].dt.hour
    hourly = hourly.groupby("hour", as_index=False).agg(
        actual_avg=("actual", "mean"),
        predicted_avg=("predicted", "mean"),
    )
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=hourly["hour"],
            y=hourly["actual_avg"],
            mode="lines+markers",
            name="Actual Avg",
            line=dict(color="#f08c00", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hourly["hour"],
            y=hourly["predicted_avg"],
            mode="lines+markers",
            name="Predicted Avg",
            line=dict(color="#1c7ed6", width=3),
        )
    )
    fig.update_layout(
        title="Average Hourly Consumption Pattern",
        height=320,
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis_title="Hour of Day",
        yaxis_title="Average Consumption (kWh)",
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0.96)",
        font=dict(color="#10243d", size=13),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e8eef7", dtick=2)
    fig.update_yaxes(showgrid=True, gridcolor="#e8eef7")
    return enforce_plot_visibility(fig)


def build_actual_vs_pred_scatter(df: pd.DataFrame) -> go.Figure:
    sample_df = df.copy()
    if len(sample_df) > 400:
        sample_df = sample_df.sample(400, random_state=42)
    low = min(sample_df["predicted"].min(), sample_df["actual"].min())
    high = max(sample_df["predicted"].max(), sample_df["actual"].max())

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=sample_df["predicted"],
            y=sample_df["actual"],
            mode="markers",
            name="Readings",
            marker=dict(
                size=8,
                color=np.where(sample_df["theft"] == 1, "#e03131", "#1c7ed6"),
                opacity=0.72,
            ),
            text=np.where(sample_df["theft"] == 1, "Theft Flag", "Normal"),
            hovertemplate="Predicted: %{x:.2f}<br>Actual: %{y:.2f}<br>Status: %{text}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[low, high],
            y=[low, high],
            mode="lines",
            name="Ideal Line",
            line=dict(color="#495057", dash="dash"),
        )
    )
    fig.update_layout(
        title="Actual vs Predicted (Closer to line = better)",
        height=320,
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis_title="Predicted",
        yaxis_title="Actual",
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0.96)",
        font=dict(color="#10243d", size=13),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e8eef7")
    fig.update_yaxes(showgrid=True, gridcolor="#e8eef7")
    return enforce_plot_visibility(fig)


def build_error_distribution(df: pd.DataFrame) -> go.Figure:
    err = np.abs(df["actual"] - df["predicted"])
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=err,
            nbinsx=24,
            marker_color="#12b886",
            name="Absolute Error",
            opacity=0.9,
        )
    )
    fig.update_layout(
        title="Prediction Error Distribution",
        height=320,
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis_title="|Actual - Predicted|",
        yaxis_title="Frequency",
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0.96)",
        font=dict(color="#10243d", size=13),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e8eef7")
    fig.update_yaxes(showgrid=True, gridcolor="#e8eef7")
    return enforce_plot_visibility(fig)


def to_csv_download(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


if "auth_ok" not in st.session_state:
    st.session_state["auth_ok"] = False
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""

USERS = {
    "admin": {"password": "admin123", "role": "Admin"},
    "operator1": {"password": "op123", "role": "Operator"},
}

st.sidebar.header("Access")

if not st.session_state["auth_ok"]:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login", use_container_width=True):
        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state["auth_ok"] = True
            st.session_state["user_name"] = username
            st.session_state["role"] = user["role"]
            st.sidebar.success(f"Welcome, {username}")
            st.rerun()
        else:
            st.sidebar.error("Invalid credentials")
    st.info("Demo credentials: admin/admin123 or operator1/op123")
    st.stop()
else:
    st.sidebar.success(f"Logged in: {st.session_state['user_name']} ({st.session_state['role']})")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state["auth_ok"] = False
        st.session_state["user_name"] = ""
        st.session_state["role"] = ""
        st.rerun()


try:
    all_data = load_data()
except Exception as exc:
    st.error(f"Unable to load data: {exc}")
    st.stop()


st.sidebar.header("Control Center")
all_meters = sorted(all_data["meter_id"].unique())
if st.session_state["role"] == "Operator":
    meters = [m for m in all_meters if m == "Meter-1001"] or [all_meters[0]]
else:
    meters = all_meters

selected_meter = st.sidebar.selectbox("Meter", meters)
run_live = st.sidebar.toggle("Live monitoring", value=False)
refresh_speed = st.sidebar.slider("Refresh (seconds)", 0.2, 2.0, 0.6, 0.1)

meter_data = all_data[all_data["meter_id"] == selected_meter].copy()
if meter_data.empty:
    st.warning("No records found for selected meter.")
    st.stop()

min_dt = meter_data["datetime"].min().date()
max_dt = meter_data["datetime"].max().date()
selected_dates = st.sidebar.date_input(
    "Date range",
    value=(min_dt, max_dt),
    min_value=min_dt,
    max_value=max_dt,
)

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_d, end_d = selected_dates
else:
    start_d = end_d = min_dt

mask = (meter_data["datetime"].dt.date >= start_d) & (meter_data["datetime"].dt.date <= end_d)
filtered_data = meter_data.loc[mask].reset_index(drop=True)

if filtered_data.empty:
    st.warning("Selected date range has no data.")
    st.stop()

latest = filtered_data.iloc[-1]
score = risk_score(filtered_data)
theft_count = int(filtered_data["theft"].sum())
record_count = len(filtered_data)
mae = float(np.mean(np.abs(filtered_data["actual"] - filtered_data["predicted"])))
peak = float(filtered_data["actual"].max())
overall_label = "HIGH RISK" if score >= 35 else "NORMAL"

recent_n = min(100, len(filtered_data))
previous_n = min(100, max(len(filtered_data) - recent_n, 1))
recent_slice = filtered_data.tail(recent_n)
previous_slice = filtered_data.head(previous_n)

recent_theft_rate = float(recent_slice["theft"].mean()) * 100
previous_theft_rate = float(previous_slice["theft"].mean()) * 100 if len(previous_slice) else 0.0
theft_delta = recent_theft_rate - previous_theft_rate

recent_mae = float(np.mean(np.abs(recent_slice["actual"] - recent_slice["predicted"])))
previous_mae = float(np.mean(np.abs(previous_slice["actual"] - previous_slice["predicted"]))) if len(previous_slice) else recent_mae
mae_delta = recent_mae - previous_mae

confidence_index = max(0.0, min(100.0, 100.0 - score))

st.markdown(
    f"""
    <div class="hero">
        <h1>GridGuard Intelligence Dashboard</h1>
        <p>Real-time anomaly tracking, theft intelligence, and operational visibility for <b>{selected_meter}</b>.</p>
        <div class="meta-row">
            <span class="meta-badge">Role: {st.session_state["role"]}</span>
            <span class="meta-badge">Window: {start_d} to {end_d}</span>
            <span class="meta-badge">User: {st.session_state["user_name"]}</span>
        </div>
        <span class="status-pill {'status-risk' if overall_label == 'HIGH RISK' else 'status-normal'}">{overall_label} | Risk Score: {score}%</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="insight-grid">
        <div class="insight-card">
            <h4>Operational Confidence</h4>
            <p>{confidence_index:.1f}% secure behavior score</p>
        </div>
        <div class="insight-card">
            <h4>Recent Theft Drift</h4>
            <p>{theft_delta:+.2f}% vs previous period</p>
        </div>
        <div class="insight-card">
            <h4>Forecast Stability</h4>
            <p>{mae_delta:+.3f} MAE shift in recent window</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Records", f"{record_count:,}")
m2.metric("Theft Flags", theft_count)
m3.metric("Theft Rate", f"{(theft_count / max(record_count, 1)) * 100:.2f}%", delta=f"{theft_delta:+.2f}%")
m4.metric("Model MAE", f"{mae:.2f}", delta=f"{mae_delta:+.3f}")
m5.metric("Peak Load", f"{peak:.2f} kWh")

e1, e2 = st.columns([1, 1.45])
with e1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.plotly_chart(build_risk_gauge(score), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
with e2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.plotly_chart(build_fleet_ranking(all_data), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

status_placeholder = st.empty()
chart_placeholder = st.empty()
st.markdown('<div class="chart-heading">Main Graph: Live Grid Load vs Predicted Baseline</div>', unsafe_allow_html=True)

if run_live:
    st.caption("Live mode running. Toggle off from the sidebar to pause simulation.")
    start_idx = 20 if len(filtered_data) > 20 else 2

    for i in range(start_idx, len(filtered_data) + 1):
        live_data = filtered_data.iloc[:i]
        is_theft = int(live_data.iloc[-1]["theft"]) == 1

        if is_theft:
            status_placeholder.error(
                f"Security Alert: Theft behavior detected for {selected_meter} at {live_data.iloc[-1]['datetime']}."
            )
        else:
            status_placeholder.success(
                f"Monitoring Normal: {selected_meter} operating within expected pattern."
            )

        fig = build_figure(
            live_data,
            f"Live Stream - {selected_meter}: Actual vs Predicted Consumption",
            is_live=True,
        )
        chart_placeholder.plotly_chart(fig, use_container_width=True)
        time.sleep(refresh_speed)
else:
    is_theft = int(latest["theft"]) == 1
    if is_theft:
        status_placeholder.error(
            f"Security Alert: Theft behavior detected for {selected_meter} at {latest['datetime']}."
        )
    else:
        status_placeholder.success(f"Monitoring Normal: {selected_meter} currently stable.")

    fig = build_figure(filtered_data, f"Historical Analysis - {selected_meter}: Consumption Overview")
    chart_placeholder.plotly_chart(fig, use_container_width=True)


tabs = ["Analytics", "Incident Center", "Data Explorer"]
if st.session_state["role"] == "Admin":
    tabs.append("Model Performance")

tab_objects = st.tabs(tabs)

with tab_objects[0]:
    st.markdown('<div class="section-title">Demand Deviation Profile</div>', unsafe_allow_html=True)
    dev_df = filtered_data.copy()
    dev_df["deviation"] = dev_df["actual"] - dev_df["predicted"]

    dev_fig = go.Figure()
    dev_fig.add_trace(
        go.Scatter(
            x=dev_df["datetime"],
            y=dev_df["deviation"],
            mode="lines",
            name="Deviation",
            line=dict(color="#495057", width=2),
            fill="tozeroy",
            fillcolor="rgba(10,132,255,0.12)",
        )
    )
    dev_fig.update_layout(
        title="Deviation Trace (Actual - Predicted)",
        height=360,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0.96)",
        font=dict(color="#10243d", size=13),
        xaxis_title="Timestamp",
        yaxis_title="Actual - Predicted",
        hovermode="x unified",
    )
    dev_fig.update_xaxes(showgrid=True, gridcolor="#e8eef7")
    dev_fig.update_yaxes(showgrid=True, gridcolor="#e8eef7", zerolinecolor="#adb5bd")
    dev_fig = enforce_plot_visibility(dev_fig)
    st.plotly_chart(dev_fig, use_container_width=True)

    st.caption("Quick read: values near zero mean model and actual usage are aligned. Big spikes indicate possible abnormal behavior.")

    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(build_theft_timeline(filtered_data), use_container_width=True)
    with g2:
        st.plotly_chart(build_hourly_profile(filtered_data), use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        st.plotly_chart(build_actual_vs_pred_scatter(filtered_data), use_container_width=True)
    with g4:
        st.plotly_chart(build_error_distribution(filtered_data), use_container_width=True)

with tab_objects[1]:
    st.markdown('<div class="section-title">Automated Action Center</div>', unsafe_allow_html=True)

    theft_logs = filtered_data[filtered_data["theft"] == 1][
        ["datetime", "meter_id", "actual", "predicted"]
    ].copy()

    if theft_logs.empty:
        st.success("No theft incidents in the selected period.")
    else:
        theft_logs["severity"] = np.where(
            np.abs(theft_logs["actual"] - theft_logs["predicted"]) > mae,
            "Critical",
            "High",
        )
        st.dataframe(theft_logs, use_container_width=True, hide_index=True)

    left, right = st.columns([1.2, 1])
    with left:
        if st.button("Dispatch Automated Incident Report", use_container_width=True):
            st.success(
                "Incident package generated: meter profile, event timeline, and geo-coordinates queued for utility authority."
            )
    with right:
        report_df = theft_logs if not theft_logs.empty else filtered_data.tail(20)
        st.download_button(
            label="Download Investigation CSV",
            data=to_csv_download(report_df),
            file_name=f"{selected_meter}_investigation_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

with tab_objects[2]:
    st.markdown('<div class="section-title">Latest Operational Logs</div>', unsafe_allow_html=True)
    st.dataframe(filtered_data.tail(30), use_container_width=True, hide_index=True)

    summary_df = (
        all_data.groupby("meter_id", as_index=False)
        .agg(
            total_records=("theft", "size"),
            theft_cases=("theft", "sum"),
            mean_actual=("actual", "mean"),
            mean_predicted=("predicted", "mean"),
        )
        .sort_values(["theft_cases", "total_records"], ascending=[False, False])
    )
    summary_df["theft_rate_%"] = (summary_df["theft_cases"] / summary_df["total_records"] * 100).round(2)

    st.markdown('<div class="section-title">Fleet Overview</div>', unsafe_allow_html=True)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

if st.session_state["role"] == "Admin":
    with tab_objects[3]:
        st.markdown('<div class="section-title">Model Performance Evaluation</div>', unsafe_allow_html=True)
        model_metrics, eval_df = evaluate_model(filtered_data)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Accuracy", f"{model_metrics['accuracy'] * 100:.2f}%")
        c2.metric("Precision", f"{model_metrics['precision'] * 100:.2f}%")
        c3.metric("Recall", f"{model_metrics['recall'] * 100:.2f}%")
        c4.metric("F1 Score", f"{model_metrics['f1'] * 100:.2f}%")

        st.caption(
            f"Adaptive deviation threshold used for theft classification: {model_metrics['threshold']:.3f} (85th percentile)."
        )

        cm = np.array(
            [
                [model_metrics["tn"], model_metrics["fp"]],
                [model_metrics["fn"], model_metrics["tp"]],
            ]
        )

        cm_fig = go.Figure(
            data=go.Heatmap(
                z=cm,
                x=["Pred: Normal", "Pred: Theft"],
                y=["Actual: Normal", "Actual: Theft"],
                colorscale="Blues",
                text=cm,
                texttemplate="%{text}",
                showscale=False,
            )
        )
        cm_fig.update_layout(
            title="Confusion Matrix",
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="rgba(255,255,255,0)",
            plot_bgcolor="rgba(255,255,255,0.96)",
        )
        cm_fig = enforce_plot_visibility(cm_fig)
        st.plotly_chart(cm_fig, use_container_width=True)

        st.dataframe(
            eval_df[["datetime", "actual", "predicted", "theft", "model_theft_pred"]].tail(30),
            use_container_width=True,
            hide_index=True,
        )

st.caption(
    "Placement-ready tip: present this as a role-aware intelligence platform with real-time monitoring, incident workflow, and measurable model governance."
)
