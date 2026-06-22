from __future__ import annotations

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="LabPulse", layout="wide")
st_autorefresh(interval=5000, key="labpulse_refresh")

st.title("LabPulse Dashboard")


def api_get(path: str):
    response = requests.get(f"{BASE_URL}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


def safe_fetch(path: str, fallback):
    try:
        return api_get(path)
    except Exception as exc:
        st.error(f"Could not load {path}: {exc}")
        return fallback


computers = safe_fetch("/computers", [])
status = safe_fetch("/latest-status", [])
alerts = safe_fetch("/alerts", [])

online_count = sum(1 for c in computers if c.get("status") == "online")
offline_count = sum(1 for c in computers if c.get("status") == "offline")

st.subheader("Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Machines", len(computers))
col2.metric("Online", online_count)
col3.metric("Offline", offline_count)
col4.metric("Recent Alerts", len(alerts))

st.divider()

left, right = st.columns([1, 1])

with left:
    st.header("Computers")
    if computers:
        st.dataframe(pd.DataFrame(computers), use_container_width=True)
    else:
        st.info("No computers found.")

with right:
    st.header("Latest Status")
    if status:
        st.dataframe(pd.DataFrame(status), use_container_width=True)
    else:
        st.info("No status data available yet.")

st.divider()

st.header("Machine History")

pc_names = [c["pc_name"] for c in computers] if computers else []
selected_pc = st.selectbox("Select a machine", pc_names) if pc_names else None

if selected_pc:
    detail = safe_fetch(f"/machine/{selected_pc}?limit=100", None)

    if detail:
        computer = detail["computer"]
        latest = detail.get("latest_snapshot")
        history = detail.get("history", [])

        machine_col1, machine_col2, machine_col3, machine_col4 = st.columns(4)
        machine_col1.metric("Machine", computer["pc_name"])
        machine_col2.metric("Status", computer.get("status", "unknown"))

        if latest:
            machine_col3.metric(
                "Health Score",
                f"{latest.get('health_score', 0.0):.1f}/100",
                latest.get("health_status", "unknown"),
            )
            machine_col4.metric("Processes", latest.get("process_count", 0))
        else:
            machine_col3.metric("Health Score", "N/A")
            machine_col4.metric("Processes", "N/A")

        if history:
            df = pd.DataFrame(history)
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df.sort_values("timestamp")

            chart_cols = [
                col
                for col in [
                    "cpu_usage",
                    "ram_usage",
                    "disk_usage",
                    "network_sent",
                    "network_recv",
                ]
                if col in df.columns
            ]

            if chart_cols:
                st.subheader("Resource Trends")
                st.line_chart(df.set_index("timestamp")[chart_cols], use_container_width=True)

            if {"top_process_name", "top_process_cpu", "top_process_memory"}.issubset(df.columns):
                st.subheader("Top Process Trend")
                st.dataframe(
                    df[[
                        "timestamp",
                        "top_process_name",
                        "top_process_cpu",
                        "top_process_memory",
                    ]].tail(10),
                    use_container_width=True,
                )
        else:
            st.info("No history available for this machine.")

st.divider()

st.header("Recent Alerts")
if alerts:
    st.dataframe(pd.DataFrame(alerts), use_container_width=True)
else:
    st.info("No alerts generated yet.")
