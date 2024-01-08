"""
tests.conftest.py
~~~~~~~~~~~~~~~~~
Test fixture for the unit test suite. All test fixture defined in conftest MUST have the word `fixture`.
"""
import json
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from api import main

ROOT = Path(__file__).joinpath("..").joinpath("..").resolve()
TEST_DATA_PATH = ROOT / "unittests" / "data"


@pytest.fixture(scope="session")
def api_client_fixture():
    """FastAPI testing client fixture."""
    return TestClient(main.APP)


# ================================= Facebook Test data begins.

FACEBOOK_TEST_DATA_PATH = TEST_DATA_PATH / "facebook"

# Facebook Message Object Test data (models/facebook/Message)

with open(str(FACEBOOK_TEST_DATA_PATH / "message_data.json")) as outfile:
    MESSAGE_DATA = json.load(outfile)
    VALID_MESSAGE_DATA = MESSAGE_DATA.get("valid")


@pytest.fixture(scope="session", params=VALID_MESSAGE_DATA)
def test_fixture_valid_message(request):
    """Test data for valid message models"""
    return request.param


# Facebook Messaging Object Test data (models/facebook/Messaging)

with open(str(FACEBOOK_TEST_DATA_PATH / "messaging_data.json")) as outfile:
    MESSAGING_DATA = json.load(outfile)
    INVALID_MESSAGING_DATA = MESSAGING_DATA.get("invalid")
    VALID_MESSAGING_DATA = MESSAGING_DATA.get("valid")


@pytest.fixture(scope="session", params=VALID_MESSAGING_DATA)
def test_fixture_valid_messaging(request):
    """Test data for valid messaging models"""
    return request.param


# Facebook Event Object Test data (models/facebook/Event)

with open(str(FACEBOOK_TEST_DATA_PATH / "event_data.json")) as outfile:
    EVENT_DATA = json.load(outfile)
    INVALID_EVENT_DATA = EVENT_DATA.get("invalid")
    VALID_EVENT_DATA = EVENT_DATA.get("valid")


@pytest.fixture(scope="session", params=VALID_EVENT_DATA)
def test_fixture_valid_event(request):
    """Test data for valid event models"""
    return request.param


@pytest.fixture(scope="session", params=INVALID_EVENT_DATA)
def test_fixture_invalid_event(request):
    """Test data for invalid event models"""
    return request.param


# ================================= Facebook Test data ends.

# ================================= Weaver Test data begins.

WEAVER_TEST_DATA_PATH = TEST_DATA_PATH / "weaver"

with open(str(WEAVER_TEST_DATA_PATH / "sound_thread_metadata_valid.yaml")) as outfile:
    METADATA_DATA = yaml.safe_load(outfile)
    VALID_ST_METADATA = METADATA_DATA.get("valid")
    INVALID_ST_METADATA = METADATA_DATA.get("invalid")


@pytest.fixture(scope="session", params=VALID_ST_METADATA)
def test_fixture_valid_st_metadata(request):
    """Test data for valid sound thread metadata models"""
    return request.param


@pytest.fixture(scope="session", params=INVALID_ST_METADATA)
def test_fixture_invalid_st_metadata(request):
    """Test data for invalid sound thread metadata models"""
    return request.param


# ================================= Weaver Test data ends.
