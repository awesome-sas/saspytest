"""
Shared fixtures and configuration for unit tests.
"""

import pytest


@pytest.fixture
def mock_sas(mocker):
    """Create a mocked SAS session object for unit testing."""
    sas = mocker.MagicMock()
    return sas
