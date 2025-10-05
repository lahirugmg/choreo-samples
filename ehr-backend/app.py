"""Flask service that mocks basic EHR capabilities for demo workflows."""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Dict, List
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

logger = logging.getLogger("ehr_service")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] ehr-service: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv("EHR_ALLOW_ORIGINS", "*").split(",")
    if origin.strip()
]
if not ALLOW_ORIGINS:
    ALLOW_ORIGINS = ["*"]

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

cors_kwargs = {"resources": {r"*": {"origins": ALLOW_ORIGINS}}}
# Flask-CORS expects a bare "*" rather than a single-item list containing it
if ALLOW_ORIGINS == ["*"]:
    cors_kwargs = {"resources": {r"*": {"origins": "*"}}}
CORS(app, **cors_kwargs)


def _iso(dt: datetime) -> str:
    """Return ISO 8601 string without microseconds for deterministic responses."""
    return dt.replace(microsecond=0).isoformat()


_PATIENT_SUMMARIES: Dict[str, Dict] = {
    "12345": {
        "demographics": {
            "name": "Jordan Matthews",
            "age": 62,
            "gender": "female",
            "mrn": "12345",
        },
        "problems": [
            "Type 2 diabetes mellitus",
            "CKD stage 3",
            "Hypertension",
        ],
        "medications": ["Metformin 1000 mg BID", "Lisinopril 20 mg daily"],
        "vitals": {
            "systolic": 128,
            "diastolic": 78,
            "heart_rate": 72,
            "weight_kg": 82.5,
            "updated_at": _iso(datetime(2024, 9, 12, 9, 45)),
        },
        "last_a1c": 7.4,
        "last_egfr": 54.0,
    },
    "12873": {
        "demographics": {
            "name": "Avery Patel",
            "age": 58,
            "gender": "female",
            "mrn": "12873",
        },
        "problems": [
            "Type 2 diabetes mellitus",
            "Chronic kidney disease stage 3",
            "Hypertension",
        ],
        "medications": ["Metformin 1000 mg BID", "Losartan 50 mg daily"],
        "vitals": {
            "systolic": 132,
            "diastolic": 82,
            "heart_rate": 76,
            "weight_kg": 79.8,
            "updated_at": _iso(datetime(2025, 9, 12, 9, 15)),
        },
        "last_a1c": 8.2,
        "last_egfr": 44.0,
    },
}

_PATIENT_LABS: Dict[str, List[Dict]] = {
    "12345": [
        {
            "name": "HbA1c",
            "value": 7.4,
            "unit": "%",
            "collected_at": _iso(datetime(2024, 9, 10, 8, 30)),
        },
        {
            "name": "HbA1c",
            "value": 7.8,
            "unit": "%",
            "collected_at": _iso(datetime(2024, 6, 5, 8, 30)),
        },
        {
            "name": "eGFR",
            "value": 54.0,
            "unit": "mL/min/1.73m2",
            "collected_at": _iso(datetime(2024, 9, 10, 8, 35)),
        },
        {
            "name": "eGFR",
            "value": 58.0,
            "unit": "mL/min/1.73m2",
            "collected_at": _iso(datetime(2024, 3, 15, 8, 35)),
        },
        {
            "name": "LDL",
            "value": 82,
            "unit": "mg/dL",
            "collected_at": _iso(datetime(2024, 9, 1, 8, 0)),
        },
    ],
    "12873": [
        {
            "name": "HbA1c",
            "value": 8.2,
            "unit": "%",
            "collected_at": _iso(datetime(2025, 9, 5, 8, 0)),
        },
        {
            "name": "HbA1c",
            "value": 8.6,
            "unit": "%",
            "collected_at": _iso(datetime(2025, 6, 2, 8, 10)),
        },
        {
            "name": "HbA1c",
            "value": 8.9,
            "unit": "%",
            "collected_at": _iso(datetime(2025, 3, 3, 8, 5)),
        },
        {
            "name": "eGFR",
            "value": 44.0,
            "unit": "mL/min/1.73m2",
            "collected_at": _iso(datetime(2025, 9, 12, 7, 55)),
        },
        {
            "name": "eGFR",
            "value": 46.0,
            "unit": "mL/min/1.73m2",
            "collected_at": _iso(datetime(2025, 6, 9, 7, 50)),
        },
        {
            "name": "eGFR",
            "value": 48.0,
            "unit": "mL/min/1.73m2",
            "collected_at": _iso(datetime(2025, 3, 10, 7, 45)),
        },
    ],
}


@app.route("/patients/<patient_id>/summary", methods=["GET"])
def get_patient_summary(patient_id: str):
    logger.info("GET /patients/%s/summary", patient_id)
    summary = _PATIENT_SUMMARIES.get(patient_id)
    if not summary:
        logger.info("Patient not found: patient_id=%s", patient_id)
        return jsonify({"detail": "Patient not found"}), 404

    logger.info(
        "Returning summary for patient_id=%s (problems=%s)",
        patient_id,
        summary.get("problems", []),
    )
    return jsonify(summary)


@app.route("/patients/<patient_id>/labs", methods=["GET"])
def get_patient_labs(patient_id: str):
    names = request.args.get("names")
    last_n = request.args.get("last_n", type=int)
    logger.info(
        "GET /patients/%s/labs names=%s last_n=%s",
        patient_id,
        names,
        last_n,
    )

    lab_history = _PATIENT_LABS.get(patient_id)
    if not lab_history:
        logger.info("Patient not found or no lab history: patient_id=%s", patient_id)
        return jsonify({"detail": "Patient not found or no lab history"}), 404

    filtered = list(lab_history)
    if names:
        allowed = {name.strip().lower() for name in names.split(",") if name.strip()}
        filtered = [lab for lab in filtered if lab["name"].lower() in allowed]

    filtered = sorted(filtered, key=lambda lab: lab["collected_at"], reverse=True)

    if last_n is not None:
        if last_n < 1:
            return jsonify({"detail": "last_n must be greater than zero"}), 422
        filtered = filtered[:last_n]

    response = {"patient_id": patient_id, "labs": filtered}
    logger.info(
        "Returning %d labs for patient_id=%s",
        len(filtered),
        patient_id,
    )
    return jsonify(response)


@app.route("/orders/medication", methods=["POST"])
def create_medication_order():
    payload = request.get_json(silent=True) or {}
    logger.info(
        "POST /orders/medication patient_id=%s medication=%s",
        payload.get("patient_id"),
        payload.get("medication"),
    )

    required_fields = {"patient_id", "medication", "dose", "route", "frequency"}
    missing = sorted(field for field in required_fields if field not in payload)
    if missing:
        logger.info("Medication order missing fields: %s", ", ".join(missing))
        return (
            jsonify({"detail": f"Missing required fields: {', '.join(missing)}"}),
            400,
        )

    order_id = f"draft-{uuid4()}"
    logger.info("Draft medication order created id=%s", order_id)
    return jsonify({"order_id": order_id, "status": "draft created"}), 201


@app.route("/evidence/search", methods=["POST"])
def search_evidence():
    payload = request.get_json(silent=True) or {}
    logger.info(
        "POST /evidence/search condition=%s comorbidity=%s",
        payload.get("condition"),
        payload.get("comorbidity"),
    )

    geo = payload.get("geo") or {}
    try:
        radius_km = float(geo["radius_km"])
    except (TypeError, KeyError, ValueError):
        return jsonify({"detail": "Invalid or missing geo.radius_km"}), 400

    guideline_ids = ["ADA-2024-DM2"]
    rct_ids = ["NCT01234567", "NCT07654321"]
    all_trials = [
        {
            "id": "NCT05566789",
            "name": "Renal Outcomes in Diabetes",
            "distance_km": 12.4,
            "eligibility_summary": "Adults 40-75 with type 2 diabetes and eGFR 45-60",
        },
        {
            "id": "NCT08899881",
            "name": "Cardiometabolic Risk Reduction Study",
            "distance_km": 48.0,
            "eligibility_summary": "Type 2 diabetes with uncontrolled A1c > 7 despite therapy",
        },
    ]

    nearby_trials = [
        trial for trial in all_trials if trial["distance_km"] <= radius_km
    ][:2]

    return jsonify(
        {
            "guideline_ids": guideline_ids,
            "rct_ids": rct_ids,
            "nearby_trials": nearby_trials,
        }
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
