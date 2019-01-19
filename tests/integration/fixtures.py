# coding: utf-8
"""
General fixtures for the integration tests
"""
import os
import pytest
import tests.integration


@pytest.fixture
def get_barestates_root():
    """
    Get states root (default env).

    :return: path to the states root.
    """
    return os.path.join(os.path.dirname(tests.integration.__file__), "root", "barestates")
