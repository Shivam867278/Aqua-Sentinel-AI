# Aqua Sentinel AI

Modern Streamlit dashboard UI for an AI-based Water Conservation and Monitoring System.

## Features

- Premium dark industrial UI with blue accents
- Streamlit dashboard with sidebar navigation
- Live simulated IoT telemetry and Plotly charts
- Animated KPI cards for flow, pressure, demand, and water loss
- Flask API backend with `/leakage`, `/quality`, and `/predict-demand`
- Extra API routes for `/health`, `/telemetry`, `/assets`, `/alerts`, and `/optimize`
- Graceful API error handling in the frontend
- Local AI simulation fallback, so buttons still work when the Flask API is offline
- Login, registration, role-aware users, and city-scoped data storage
- SQLite database for users, auth tokens, alerts, saved predictions, and control actions
- Citizen complaint/ticket system with staff status updates
- Citizen 1-5 star service rating and feedback system
- Supervisory water-system control requests for flow, pressure, pH, and chemical dosing
- Automatic alarm detection for leakage and harmful water-system scenarios
- Citizen water account dashboard with bill, tank level, motor status, quality report, and flow meter
- Asset health table, alert center, AI control room, and visual analytics
- Environment-driven configuration for local and deployment use
- Basic backend tests
- Docker and Docker Compose support

## Project Structure

```text
.
|-- app.py                  # Streamlit frontend
|-- api_client.py           # Frontend API helper
|-- backend.py              # Flask API backend
|-- config.py               # Environment-driven settings
|-- database.py             # SQLite persistence and authentication helpers
|-- local_ai.py             # Offline fallback AI simulation
|-- response_utils.py       # Standard API response helpers
|-- simulator.py            # Live IoT data simulator
|-- styles.py               # Custom premium CSS
|-- ui_components.py        # Reusable Streamlit UI components
|-- validation.py           # Backend validation helpers
|-- tests/
|   `-- test_backend.py
|-- Dockerfile.api
|-- Dockerfile.streamlit
|-- docker-compose.yml
|-- requirements.txt
|-- run_backend.bat
|-- run_frontend.bat
`-- run_project.bat
```

## Setup

Install Python 3.10 or newer, then run:

```bash
pip install -r requirements.txt
```

## Run On Windows

Fastest option:

```text
Double-click run_project.bat
```

This installs dependencies, starts the Flask API, and starts the Streamlit dashboard.

Manual option:

Terminal 1:

```bash
python backend.py
```

Terminal 2:

```bash
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

If `python` does not work, use:

```bash
py -3 backend.py
py -3 -m streamlit run app.py
```

## Environment Configuration

Copy `.env.example` values into your deployment environment as needed.

Important variables:

```text
AQUA_API_BASE_URL=http://127.0.0.1:5000
AQUA_ENABLE_LOCAL_FALLBACK=true
AQUA_DEVELOPER_NAME=Shivam
AQUA_ENV=development
AQUA_DATABASE_URL=sqlite:///data/aqua_sentinel.db
AQUA_AUTH_TOKEN_HOURS=12
```

## Demo Login Credentials

```text
Admin:    admin@aqua.local / admin123
Operator: operator@aqua.local / operator123
Citizen:  citizen@aqua.local / citizen123
```

New citizens can also register from the login screen.

## Data Storage

The backend stores platform data in SQLite:

```text
data/aqua_sentinel.db
```

Stored data includes users, city profiles, login tokens, alerts, predictions, AI control actions, citizen complaints, service ratings, and audited control requests.

## Citizen Complaints

Logged-in citizens can submit complaints from the dashboard:

- Water leakage
- Low pressure
- Water quality
- No water supply
- Billing/service issues
- Other city water issues

Admins and operators can view all complaints in their city and update status:

```text
Open -> In Progress -> Resolved
```

Complaint APIs:

```text
GET    /complaints
POST   /complaints
PATCH  /complaints/<complaint_id>
```

## Service Ratings

Logged-in users can rate the city water service from 1 to 5 stars and leave optional feedback.
Admins and operators can view satisfaction summary and recent feedback.

Rating APIs:

```text
GET   /ratings
POST  /ratings
```

## Water System Control

Admins and operators can create safe supervisory control requests for:

- Flow rate setpoint
- Pressure setpoint
- pH target
- Chlorine dose
- Coagulant dose

The software stores the request, validates safe ranges, and requires admin approval before marking it approved or executed.
This project does not directly control real pumps, valves, or chemical dosing hardware. Real-world actuation must be connected only through certified PLC/SCADA integrations and approved safety procedures.

Control APIs:

```text
GET    /controls
POST   /controls
PATCH  /controls/<control_id>
```

## Automatic Alarms

The platform can automatically scan live telemetry and raise alarms for:

- Probable leakage
- Pipe burst/acoustic leakage signature
- Dangerous pressure
- Unsafe turbidity
- High non-revenue water loss
- pH outside safe range
- Chlorine dosing outside target range

Alarm API:

```text
POST /monitoring/scan
```

## Citizen Water Account

Logged-in users can view:

- Water bill and due date
- Monthly consumption
- Household tank level
- Motor status and last run
- Water quality report
- Flow meter readings
- Daily and monthly usage

Account API:

```text
GET /citizen/water-account
```

## Industry-Ready Additions

- Environment-based configuration in `config.py`
- `.env.example` for deployment settings
- Standard API response format with request IDs and timestamps
- Backend input validation with proper `400` errors
- Authentication APIs: `/auth/login`, `/auth/register`, and `/auth/me`
- Error handlers for missing endpoints and server failures
- Local AI fallback can be enabled or disabled with `AQUA_ENABLE_LOCAL_FALLBACK`
- Docker and Docker Compose files for container deployment
- Basic backend tests in `tests/test_backend.py`

## Run Tests

```bash
pytest
```

In VS Code, you can also use:

```text
Terminal > Run Task > Run backend tests
```

## Run With Docker

```bash
docker compose up --build
```

Dashboard:

```text
http://localhost:8501
```

API:

```text
http://localhost:5000/health
```

## API Response Format

Successful API responses use this shape:

```json
{
  "success": true,
  "message": "ok",
  "data": {},
  "request_id": "uuid",
  "timestamp": "UTC timestamp"
}
```

Error responses use:

```json
{
  "success": false,
  "message": "error message",
  "details": {},
  "request_id": "uuid",
  "timestamp": "UTC timestamp"
}
```
