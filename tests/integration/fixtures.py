# coding: utf-8
"""
General fixtures for the integration tests
"""
import os
import pytest
import tests.integration

COMMON_INTEGRATION_STATES_ROOT = os.path.join(os.path.dirname(tests.integration.__file__), "root")


@pytest.fixture
def get_barestates_root():
    """
    Get bare data fake states root (default env).

    :return: path to the states root.
    """
    return os.path.join(COMMON_INTEGRATION_STATES_ROOT, "barestates")

@pytest.fixture
def get_states_root():
    """
    Get real states root (default env).

    :return: path to the states root.
    """
    return os.path.join(COMMON_INTEGRATION_STATES_ROOT, "states")
