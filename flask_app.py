from __future__ import annotations

from functools import lru_cache
from threading import Event, Lock
from typing import Any

import numpy as np
import pandas as pd
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO


app = Flask(__name__)
app.secret_key = "gridguard-dev-secret-key"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


USERS = {
    "admin": {"password": "admin123", "role": "Admin"},
    "operator1": {"password": "op123", "role": "Operator"},
}
_stream_stops: dict[str, Event] = {}
_stream_lock = Lock()


def _risk_score(df: pd.DataFrame) -> float:
    theft_rate = float(df["theft"].mean()) if len(df) else 0.0
    deviation = np.abs(df["actual"] - df["predicted"])
    scale = float(df["actual"].mean() + 1e-6)
    rel_deviation = float(deviation.mean() / scale) if len(df) else 0.0
    raw = (0.65 * theft_rate + 0.35 * min(rel_deviation, 1.0)) * 100
    return round(min(raw, 100.0), 2)


def _prepare_filtered_data(
    *,
    current_role: str,
    selected_meter: str | None,
    start_str: str | None,
    end_str: str | None,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str], str, pd.Timestamp, pd.Timestamp]:
    all_data = load_data().copy()
    meters = sorted(all_data["meter_id"].unique().tolist())

    if current_role == "Operator":
        operator_meters = [m for m in meters if m == "Meter-1001"]
        if operator_meters:
            meters = operator_meters

    selected = selected_meter or (meters[0] if meters else "")
    if selected not in meters and meters:
        selected = meters[0]

    meter_data = all_data[all_data["meter_id"] == selected].copy()
    if meter_data.empty:
        meter_data = all_data.copy()
        selected = meter_data["meter_id"].iloc[0]

    min_date = meter_data["datetime"].min().date()
    max_date = meter_data["datetime"].max().date()

    start_date = pd.to_datetime(start_str or str(min_date), errors="coerce")
    end_date = pd.to_datetime(end_str or str(max_date), errors="coerce")
    if pd.isna(start_date):
        start_date = pd.Timestamp(min_date)
    if pd.isna(end_date):
        end_date = pd.Timestamp(max_date)

    mask = (meter_data["datetime"].dt.date >= start_date.date()) & (
        meter_data["datetime"].dt.date <= end_date.date()
    )
    filtered = meter_data.loc[mask].copy()
    if filtered.empty:
        filtered = meter_data.copy()

    filtered = filtered.sort_values("datetime").reset_index(drop=True)
    return all_data, filtered, meters, selected, start_date, end_date


@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    data = pd.read_csv("Final_Model_Output.csv")
    data.columns = data.columns.str.strip().str.lower()

    datetime_col = next((c for c in data.columns if "date" in c or "time" in c), None)
    actual_col = next((c for c in data.columns if "actual" in c), None)
    pred_col = next((c for c in data.columns if "pred" in c), None)
    if not datetime_col or not actual_col or not pred_col:
        raise ValueError("Dataset must include datetime/time, actual and predicted columns.")

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
    data["actual"] = pd.to_numeric(data["actual"], errors="coerce")
    data["predicted"] = pd.to_numeric(data["predicted"], errors="coerce")
    data["theft"] = pd.to_numeric(data["theft"], errors="coerce").fillna(0).astype(int)
    data = data.dropna(subset=["datetime", "actual", "predicted"]).copy()

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

    return data.sort_values("datetime").reset_index(drop=True)


@app.route("/")
def dashboard() -> str:
    if not session.get("auth_ok"):
        return redirect(url_for("login"))

    current_user = session.get("user_name", "guest")
    current_role = session.get("role", "Operator")

    selected_meter = request.args.get("meter", "")
    mode = request.args.get("mode", "static")
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    all_data, filtered, meters, selected_meter, start_date, end_date = _prepare_filtered_data(
        current_role=current_role,
        selected_meter=selected_meter,
        start_str=start_str,
        end_str=end_str,
    )
    latest = filtered.iloc[-1]
    theft_count = int(filtered["theft"].sum())
    record_count = int(len(filtered))
    theft_rate = float(theft_count / max(record_count, 1) * 100)
    mae = float(np.mean(np.abs(filtered["actual"] - filtered["predicted"])))
    peak = float(filtered["actual"].max())
    score = _risk_score(filtered)
    filtered["deviation_abs"] = np.abs(filtered["actual"] - filtered["predicted"])
    anomaly_threshold = float(filtered["deviation_abs"].quantile(0.85))
    anomaly_rate = float((filtered["deviation_abs"] >= anomaly_threshold).mean() * 100)
    grid_health = round(max(0.0, 100.0 - score), 2)

    main_labels = filtered["datetime"].dt.strftime("%Y-%m-%d %H:%M").tolist()
    actual_vals = filtered["actual"].round(4).tolist()
    pred_vals = filtered["predicted"].round(4).tolist()
    theft_vals = filtered["theft"].astype(int).tolist()

    daily = (
        filtered.assign(day=filtered["datetime"].dt.strftime("%Y-%m-%d"))
        .groupby("day", as_index=False)
        .agg(theft_cases=("theft", "sum"))
    )
    daily_labels = daily["day"].tolist()
    daily_values = daily["theft_cases"].astype(int).tolist()

    hourly = (
        filtered.assign(hour=filtered["datetime"].dt.hour)
        .groupby("hour", as_index=False)
        .agg(actual_avg=("actual", "mean"), predicted_avg=("predicted", "mean"))
    )
    hourly_labels = hourly["hour"].astype(int).tolist()
    hourly_actual = hourly["actual_avg"].round(4).tolist()
    hourly_pred = hourly["predicted_avg"].round(4).tolist()

    fleet = (
        all_data.groupby("meter_id", as_index=False)
        .agg(theft_cases=("theft", "sum"), total_records=("theft", "size"))
        .sort_values("theft_cases", ascending=False)
    )
    fleet["theft_rate"] = (fleet["theft_cases"] / fleet["total_records"] * 100).round(2)

    err = np.abs(filtered["actual"] - filtered["predicted"])
    hist_values, hist_bins = np.histogram(err, bins=18)
    hist_labels = [f"{hist_bins[i]:.2f}-{hist_bins[i + 1]:.2f}" for i in range(len(hist_values))]

    scatter_points = (
        filtered[["predicted", "actual", "theft"]]
        .sample(min(400, len(filtered)), random_state=42)
        .to_dict(orient="records")
    )

    incidents_df = filtered[filtered["theft"] == 1].copy().sort_values("datetime", ascending=False)
    if not incidents_df.empty:
        severity_cutoff = float(incidents_df["deviation_abs"].quantile(0.7))
        incidents_df["severity"] = np.where(incidents_df["deviation_abs"] >= severity_cutoff, "Critical", "High")
        incidents_df = incidents_df.head(12)
    incidents = [
        {
            "datetime": row["datetime"].strftime("%Y-%m-%d %H:%M"),
            "actual": round(float(row["actual"]), 3),
            "predicted": round(float(row["predicted"]), 3),
            "deviation": round(float(row["deviation_abs"]), 3),
            "severity": row["severity"] if "severity" in row else "High",
        }
        for _, row in incidents_df.iterrows()
    ]

    chart_data: dict[str, Any] = {
        "mode": mode,
        "main_labels": main_labels,
        "actual_vals": actual_vals,
        "pred_vals": pred_vals,
        "theft_vals": theft_vals,
        "daily_labels": daily_labels,
        "daily_values": daily_values,
        "hourly_labels": hourly_labels,
        "hourly_actual": hourly_actual,
        "hourly_pred": hourly_pred,
        "fleet_labels": fleet["meter_id"].tolist(),
        "fleet_values": fleet["theft_rate"].tolist(),
        "hist_labels": hist_labels,
        "hist_values": hist_values.astype(int).tolist(),
        "scatter_points": scatter_points,
        "risk_score": score,
        "status": "HIGH RISK" if score >= 35 else "NORMAL",
        "live_stream_interval_seconds": 1,
        "live_query": {
            "meter": selected_meter,
            "start": start_date.date().isoformat(),
            "end": end_date.date().isoformat(),
        },
    }

    return render_template(
        "index.html",
        meters=meters,
        selected_meter=selected_meter,
        start_date=start_date.date().isoformat(),
        end_date=end_date.date().isoformat(),
        mode=mode,
        metrics={
            "records": record_count,
            "theft_flags": theft_count,
            "theft_rate": round(theft_rate, 2),
            "mae": round(mae, 3),
            "peak": round(peak, 3),
            "risk": score,
            "anomaly_rate": round(anomaly_rate, 2),
            "grid_health": grid_health,
            "status": "HIGH RISK" if score >= 35 else "NORMAL",
            "latest_time": latest["datetime"].strftime("%Y-%m-%d %H:%M"),
        },
        chart_data=chart_data,
        incidents=incidents,
        current_user=current_user,
        current_role=current_role,
    )


@app.route("/login", methods=["GET", "POST"])
def login() -> str:
    if session.get("auth_ok"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = USERS.get(username)
        if user and user["password"] == password:
            session["auth_ok"] = True
            session["user_name"] = username
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout() -> Any:
    session.clear()
    return redirect(url_for("login"))


def _stream_live_points(sid: str, filtered: pd.DataFrame, stop_event: Event, interval_seconds: float = 1.0) -> None:
    if filtered.empty:
        socketio.emit("live_error", {"message": "No data available for live stream."}, to=sid)
        return

    idx = 0
    total = len(filtered)
    while not stop_event.is_set():
        row = filtered.iloc[idx]
        socketio.emit(
            "live_point",
            {
                "datetime": row["datetime"].strftime("%Y-%m-%d %H:%M"),
                "actual": round(float(row["actual"]), 4),
                "predicted": round(float(row["predicted"]), 4),
                "theft": int(row["theft"]),
                "index": idx,
                "total": total,
            },
            to=sid,
        )
        idx = (idx + 1) % total
        socketio.sleep(interval_seconds)


@socketio.on("connect")
def socket_connect() -> bool:
    if not session.get("auth_ok"):
        return False

    role = session.get("role", "Operator")
    selected_meter = request.args.get("meter")
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    _, filtered, _, _, _, _ = _prepare_filtered_data(
        current_role=role,
        selected_meter=selected_meter,
        start_str=start_str,
        end_str=end_str,
    )

    sid = request.sid
    stop_event = Event()
    with _stream_lock:
        previous = _stream_stops.pop(sid, None)
        if previous is not None:
            previous.set()
        _stream_stops[sid] = stop_event

    socketio.start_background_task(_stream_live_points, sid, filtered, stop_event, 1.0)
    return True


@socketio.on("disconnect")
def socket_disconnect() -> None:
    sid = request.sid
    with _stream_lock:
        stop_event = _stream_stops.pop(sid, None)
    if stop_event is not None:
        stop_event.set()


if __name__ == "__main__":
    socketio.run(app, debug=True, host="127.0.0.1", port=5000)
