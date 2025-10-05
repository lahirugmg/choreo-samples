# EHR Service

Flask backend that exposes a minimal electronic health record API used by the LangGraph agents.

## Setup
1. Ensure Python 3.10+ is available.
2. (Optional) Create a virtual environment.
3. Copy environment defaults with `cp ehr-backend/.env.example ehr-backend/.env` and adjust as needed.
4. From the repository root run `pip install -r ehr-backend/requirements.txt`.

## Run
```bash
python -m flask --app ehr-backend.app run --host 0.0.0.0 --port 8001 --debug
```

The OpenAPI contract is available in `ehr-backend/openapi.yaml` for reference.

## Endpoints
- `GET /patients/{id}/summary` — demographics, problem list, medications, vitals, and latest HbA1c/eGFR.
- `GET /patients/{id}/labs?names=HbA1c,eGFR&last_n=6` — retrieve lab history with optional filters.
- `POST /orders/medication` — accept a medication order payload and return a draft acknowledgement.
- `POST /evidence/search` — search guidelines, trials, and RCTs with basic geo filtering.
