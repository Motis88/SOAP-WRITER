"""
Tests for the PDF parsing service.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import io
import pytest
from unittest.mock import patch, MagicMock

from app.services.pdf_service import (
    _detect_report_type,
    _extract_tests,
    _extract_snap,
    _parse_test_line,
    parse_pdf,
    CBC_TESTS,
    CHEMISTRY_TESTS,
)
from app.models import LabResult


def test_detect_procyte():
    assert _detect_report_type("ProCyte CBC Report WBC RBC") == "procyte"


def test_detect_catalyst():
    assert _detect_report_type("Catalyst Chemistry Panel ALT AST") == "catalyst"


def test_detect_snap():
    assert _detect_report_type("SNAP 4Dx Plus Test") == "snap"


def test_detect_ua():
    assert _detect_report_type("Urinalysis Report USG pH") == "ua"


def test_detect_unknown():
    assert _detect_report_type("random text with no keywords") == "unknown"


def test_parse_test_line_basic():
    line = "WBC  7.5  10^3/µL  5.0-16.0"
    result = _parse_test_line(line, "WBC")
    assert result is not None
    assert result.test == "WBC"
    assert result.value == "7.5"


def test_parse_test_line_with_flag():
    line = "ALT  320  U/L  12-118  H"
    result = _parse_test_line(line, "ALT")
    assert result is not None
    assert result.flag is not None


def test_extract_snap_positive():
    text = "Heartworm Ag: Positive\nEhrlichia: Negative\nAnaplasma: Positive"
    results = _extract_snap(text)
    assert len(results) == 3
    positives = [r for r in results if r.value.lower() == "positive"]
    assert len(positives) == 2


def test_extract_tests_from_cbc_text():
    text = """
ProCyte CBC
WBC  8.2  10^3/uL  5.0-16.0
RBC  6.5  10^6/uL  5.5-8.5  L
HGB  14.0  g/dL  12.0-18.0
PLT  250  10^3/uL  200-500
"""
    results = _extract_tests(text, CBC_TESTS)
    test_names = [r.test for r in results]
    assert "WBC" in test_names
    assert "RBC" in test_names
    assert "PLT" in test_names


def test_parse_pdf_with_empty_bytes():
    """Empty PDF should return partial_extraction flag."""
    with patch("app.services.pdf_service._extract_pdf_text", return_value=("", False)):
        result = parse_pdf(b"")
        assert "partial_extraction" in result.flags


def test_parse_pdf_unknown_format():
    with patch(
        "app.services.pdf_service._extract_pdf_text",
        return_value=("some random content that is not IDEXX", False),
    ):
        result = parse_pdf(b"dummy")
        assert "unknown_pdf_format" in result.flags
