# Victory Trading Bot Dashboard

This directory contains a Streamlit dashboard for real-time visualization of trading metrics and audit events.

## How to Use

1. **Install Streamlit and dependencies:**
   ```sh
   pip install streamlit pandas requests
   ```

2. **Start the Victory Trading Bot in live mode** (ensure Prometheus metrics and audit logs are being generated).

3. **Run the dashboard:**
   ```sh
   streamlit run src/victory_bot/dashboard/streamlit_dashboard.py
   ```

4. **Open your browser to** [http://localhost:8501](http://localhost:8501) to view live metrics and audit events.

## Features
- Live trade profit and count per symbol
- Recent audit events
- Auto-refresh every 10 seconds

---

For advanced visualization, connect Prometheus to Grafana and build custom dashboards.
