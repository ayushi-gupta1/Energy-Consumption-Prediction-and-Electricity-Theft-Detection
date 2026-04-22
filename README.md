# GridGuard: Smart Energy Theft Detection Dashboard

A placement-ready energy analytics project with two frontends:
- `flask_app.py` + Jinja2 + Bootstrap (professional web dashboard with auth, dark mode, live charts)
- `app.py` Streamlit dashboard (interactive ML-style monitoring app)

## Project Structure
- `flask_app.py`: Main Flask app (auth, role access, analytics)
- `templates/`: Jinja HTML templates (`index.html`, `login.html`)
- `static/`: CSS + JavaScript assets for Flask UI
- `app.py`: Streamlit dashboard
- `backend.py`: Data loading helpers
- `Final_Model_Output.csv`: Input dataset

## Features
- Theft detection visualization (actual vs predicted consumption)
- Live and static dashboard modes
- Role-based login
  - Admin: full meter access
  - Operator: restricted meter view
- Advanced analytics charts
  - Daily theft trend
  - Hourly pattern
  - Actual vs predicted scatter
  - Error distribution
  - Fleet theft comparison
  - Risk gauge
- Incident feed with severity labels
- Dark mode UI with theme toggle

## Demo Credentials
- `admin / admin123`
- `operator1 / op123`

## Requirements
Install dependencies:

```powershell
pip install flask flask-socketio simple-websocket pandas numpy streamlit plotly
```

## Run Flask Dashboard (Recommended)

```powershell
cd c:\ayushi
python flask_app.py
```

Open in browser:
- `http://127.0.0.1:5000/login`

## Run Streamlit Dashboard (Alternative)

```powershell
cd c:\ayushi
streamlit run app.py
```

Open in browser:
- `http://localhost:8501`

## Optional: Virtual Environment (VS Code)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install flask flask-socketio simple-websocket pandas numpy streamlit plotly
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Notes
- Dataset columns are auto-detected for datetime, actual, predicted, and theft/flag columns.
- If meter IDs are missing, synthetic meter IDs are generated.
- Flask app runs on port `5000` by default.

## Future Improvements
- Store users and alerts in a database (SQLite/PostgreSQL)
- Export PDF incident reports
- Add REST API for mobile/IoT integration
- Deploy to Render/Vercel with CI pipeline
