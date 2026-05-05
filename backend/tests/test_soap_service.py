"""
Tests for the SOAP structuring service.
Verifies that text is classified correctly without adding medical reasoning.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.services.soap_service import structure_text
from app.models import SOAPNote


def test_basic_subjective_extraction():
    """Owner complaint should land in subjective."""
    text = "כלב בן 5, הקאות יומיים"
    note = structure_text(text)
    assert isinstance(note, SOAPNote)
    # At least one subjective item
    assert note.subjective
    assert note.subjective != ["לא נמסר"]


def test_temperature_extracted_to_vitals():
    """Temperature mention should be extracted to vitals."""
    text = "בבדיקה חום 39.5"
    note = structure_text(text)
    assert note.objective.vitals.temp == "39.5"


def test_heart_rate_extracted():
    """Heart rate should be extracted."""
    text = "דופק 120 בדקה"
    note = structure_text(text)
    assert note.objective.vitals.hr == "120"


def test_assessment_and_plan_empty():
    """A and P must always be empty strings."""
    text = "כלב בן 5, הקאות, חום 39.5, דופק 100"
    note = structure_text(text)
    assert note.assessment == ""
    assert note.plan == ""


def test_empty_text_returns_missing_data_flag():
    note = structure_text("")
    assert "missing_data" in note.flags


def test_unclear_text_flagged():
    text = "?? לא ברור"
    note = structure_text(text)
    assert "unclear_text" in note.flags


def test_english_vitals_extracted():
    text = "Physical exam: temp 38.9, HR 85, RR 22"
    note = structure_text(text)
    assert note.objective.vitals.temp == "38.9"
    assert note.objective.vitals.hr == "85"
    assert note.objective.vitals.rr == "22"


def test_no_extra_info_added():
    """
    The note must not contain any text not present in the input.
    We do a basic check: subjective items must be substrings of or
    closely derived from the input.
    """
    text = "כלב בן 3, לא אוכל מאתמול"
    note = structure_text(text)
    # No fabricated text
    for item in note.subjective:
        if item != "לא נמסר":
            # Each subjective item should derive from input words
            input_words = set(text.split())
            item_words = set(item.replace("[לא ברור] ", "").split())
            assert item_words.issubset(input_words) or any(
                word in text for word in item_words
            )
