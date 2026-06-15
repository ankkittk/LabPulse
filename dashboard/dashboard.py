import pandas as pd
import requests
import streamlit as st

from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=1000, key="labpulse_refresh")

st.set_page_config(page_title="LabPulse")

st.title("LabPulse Dashboard")

BASE_URL = "http://127.0.0.1:8000"


computers = requests.get(f"{BASE_URL}/computers").json()
status = requests.get(f"{BASE_URL}/latest-status").json()
alerts = requests.get(f"{BASE_URL}/alerts").json()


st.header("Computers")

if computers:
    st.dataframe(pd.DataFrame(computers))


st.header("Latest Status")

if status:
    st.dataframe(pd.DataFrame(status))


st.header("Recent Alerts")

if alerts:
    st.dataframe(pd.DataFrame(alerts))
