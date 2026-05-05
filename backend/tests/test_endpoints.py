"""
Integration tests for the FastAPI endpoints.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_structure_endpoint_basic():
    resp = client.post(
        "/api/structure",
        json={"text": "כלב בן 5, הקאות יומיים, בבדיקה חום 39.5"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "subjective" in data
    assert "objective" in data
    assert data["assessment"] == ""
    assert data["plan"] == ""


def test_structure_endpoint_empty_text():
    resp = client.post("/api/structure", json={"text": ""})
    assert resp.status_code == 400


def test_structure_endpoint_vitals_extracted():
    resp = client.post(
        "/api/structure",
        json={"text": "חום 38.9 דופק 100 נשימה 24"},
    )
    assert resp.status_code == 200
    data = resp.json()
    vitals = data["objective"]["vitals"]
    assert vitals["temp"] == "38.9"
    assert vitals["hr"] == "100"
    assert vitals["rr"] == "24"


def test_parse_pdf_endpoint_no_pdf():
    """Uploading a non-PDF should be rejected or handled."""
    resp = client.post(
        "/api/parse-pdf",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    # Should return 400 for non-PDF
    assert resp.status_code == 400


def test_process_endpoint_text_only():
    resp = client.post(
        "/api/process",
        data={"text": "חתול בת 3, שלשול 3 ימים, בדיקה חום 40"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["assessment"] == ""
    assert data["plan"] == ""
    assert data["objective"]["vitals"]["temp"] == "40"
