# LabPulse

LabPulse is a distributed computer lab monitoring and alerting system designed to monitor multiple machines from a central location.

The system collects operating system resource metrics from monitored computers and sends them to a central server using TCP sockets. The server stores monitoring data in MySQL and exposes APIs for visualization through a Streamlit dashboard.

---

## Problem Statement

In a computer laboratory containing multiple machines, administrators often need to monitor:

* Which systems are online
* CPU utilization
* Memory utilization
* Disk utilization
* System health alerts

Checking each machine manually is inefficient and does not provide historical insights.

LabPulse solves this problem through a centralized monitoring architecture.

---

## Features Implemented

### Agent Monitoring

* CPU Usage Monitoring
* RAM Usage Monitoring
* Disk Usage Monitoring
* Hostname Identification
* Timestamped Resource Collection

### Network Communication

* TCP Socket Based Communication
* Client-Server Architecture
* JSON Data Serialization

### Backend Processing

* Multi-client TCP Listener
* Monitoring Data Processing
* Alert Evaluation Engine

### Database Persistence

* Computer Registration
* Historical Resource Storage
* Alert Storage
* Status Tracking

### Dashboard

* Computer Status View
* Latest Resource Metrics
* Alert Visualization

---

## System Architecture

```text
+----------------------+
| Streamlit Dashboard |
+----------+-----------+
           |
           | REST API
           v
+----------------------+
|     FastAPI API      |
+----------+-----------+
           |
           v
+----------------------+
|       MySQL DB       |
+----------+-----------+
           ^
           |
+----------+-----------+
|      TCP Listener    |
+----------+-----------+
           ^
           |
   -------------------
   |        |        |
   v        v        v

+-------+ +-------+ +-------+
|Agent 1| |Agent 2| |Agent 3|
+-------+ +-------+ +-------+
```

---

## Technology Stack

### Programming Language

* Python

### Operating Systems

* psutil

### Computer Networks

* TCP Sockets
* JSON Serialization

### Backend

* FastAPI
* Uvicorn

### Database

* MySQL
* mysql-connector-python

### Dashboard

* Streamlit

---

## Database Schema

### computers

Stores registered computers and their status.

```sql
id
pc_name
ip_address
last_seen
status
```

### resource_snapshots

Stores historical monitoring data.

```sql
id
computer_id
cpu_usage
ram_usage
disk_usage
timestamp
```

### alerts

Stores generated alerts.

```sql
id
computer_id
alert_type
message
timestamp
```

---

## Project Structure

```text
LabPulse/
│
├── agent/
│   ├── agent.py
│   ├── collector.py
│   └── sender.py
│
├── api/
│   └── routes.py
│
├── config/
│   └── settings.py
│
├── dashboard/
│   └── dashboard.py
│
├── database/
│   └── schema.sql
│
├── server/
│   ├── alert_manager.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── tcp_listener.py
│
├── .env.example
├── README.md
└── requirements.txt
```

---

## How to Run

### 1. Create Database

```sql
CREATE DATABASE labpulse;
```

Execute:

```text
database/schema.sql
```

to create all tables.

---

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Start TCP Monitoring Server

```bash
python -m server.main
```

---

### 4. Start Monitoring Agent

```bash
python -m agent.agent
```

---

### 5. Start FastAPI

```bash
uvicorn server.app:app --reload
```

API Documentation:

```text
http://127.0.0.1:8000/docs
```

---

### 6. Start Dashboard

```bash
streamlit run dashboard/dashboard.py
```

---

## Sample Alert

```text
[ALERT] HIGH_DISK - BT01467: Disk at 97.7% (threshold 90%)
```

---

## Future Enhancements

* Process Monitoring
* Offline Machine Detection
* Historical Trend Graphs
* Health Score Computation
* Auto-refresh Dashboard
* WebSocket-based Real-Time Updates
* Multi-Lab Monitoring
* Advanced Analytics

```
```
