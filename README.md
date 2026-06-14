# LabPulse

Distributed Computer Lab Monitoring and Alerting System.

## Architecture

Agent (psutil)
    ↓
TCP Socket
    ↓
FastAPI Backend
    ↓
MySQL

Streamlit Dashboard
    ↓
FastAPI APIs

## Tech Stack

- Python
- TCP Sockets
- FastAPI
- MySQL
- Streamlit
- psutil