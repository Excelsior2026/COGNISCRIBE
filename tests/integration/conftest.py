"""Fixtures for integration tests."""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def integration_client():
    """Create test client for integration tests."""
    return TestClient(app)


@pytest.fixture
def sample_transcript_with_phi():
    """Sample transcript containing PHI."""
    return (
        "Patient John Doe, medical record number 12345, "
        "Social Security Number 123-45-6789, was admitted on January 15, 2023. "
        "The patient's date of birth is 05/20/1980."
    )


@pytest.fixture
def sample_clean_transcript():
    """Sample transcript without PHI."""
    return (
        "This lecture covers the cardiovascular system. "
        "The heart is a muscular organ that pumps blood throughout the body. "
        "It consists of four chambers: two atria and two ventricles."
    )


@pytest.fixture
def sample_summary_response():
    """Sample structured summary response."""
    return """### Learning Objectives
Understand the structure and function of the cardiovascular system

### Core Concepts
The heart is a four-chambered pump
Blood circulation follows systemic and pulmonary pathways

### Clinical Terms
Atrium: Upper chamber of the heart
Ventricle: Lower chamber of the heart
Systole: Contraction phase
Diastole: Relaxation phase

### Procedures
Cardiac auscultation technique
Blood pressure measurement protocol

### Summary
This lecture provided an overview of cardiovascular anatomy and physiology,
emphasizing the heart's role in maintaining circulation.
"""
