"""
Unit tests for QueryRouter intent detection.
Run: python -m pytest tests/test_query_router.py -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src/database"))

import pytest
from query_router import QueryRouter

router = QueryRouter()


# ── Personal intent ────────────────────────────────────────

@pytest.mark.parametrize("query", [
    "How many leaves do I have?",
    "What is my leave balance?",
    "What is my CTC?",
    "What is my salary?",
    "What is my performance rating?",
    "Who is my manager?",
    "What is my designation?",
    "When is my performance review?",
    "Am I eligible for a promotion?",
    "How much do I earn?",
])
def test_personal_intent(query):
    assert router.detect_intent(query) == "personal", f"Expected personal for: {query}"


# ── Hybrid intent ──────────────────────────────────────────

@pytest.mark.parametrize("query", [
    "Am I eligible for WFH?",
    "Can I work from home?",
    "Am I on a PIP?",
    "When will I get promoted?",
    "Am I eligible for a bonus?",
])
def test_hybrid_intent(query):
    assert router.detect_intent(query) == "hybrid", f"Expected hybrid for: {query}"


# ── Policy intent ──────────────────────────────────────────

@pytest.mark.parametrize("query", [
    "What is the WFH policy?",
    "How do I apply for leave?",
    "What is the PIP process?",
    "What certifications are supported?",
    "What is the travel expense policy?",
    "How many days of annual leave does the company provide?",
    "What is the grievance process?",
    "What is the notice period policy?",
    "What is the dress code?",
    "What is the IT security policy?",
])
def test_policy_intent(query):
    assert router.detect_intent(query) == "policy", f"Expected policy for: {query}"


# ── Regression: known false-positive fixes ─────────────────

def test_pip_policy_not_hybrid():
    """'What is the PIP process' must not match hybrid (the 'i' in 'is' was a false positive)."""
    assert router.detect_intent("What is the PIP process?") == "policy"

def test_wfh_policy_not_hybrid():
    """'What is the WFH policy' must route to policy, not hybrid."""
    assert router.detect_intent("What is the WFH policy?") == "policy"

def test_my_pip_is_hybrid():
    """'Am I on a PIP' or 'my PIP' must still route to hybrid."""
    assert router.detect_intent("Am I on a performance improvement plan?") == "hybrid"

def test_case_insensitive():
    """Intent detection must be case-insensitive."""
    assert router.detect_intent("WHAT IS MY CTC?") == "personal"
    assert router.detect_intent("what is the wfh policy?") == "policy"
