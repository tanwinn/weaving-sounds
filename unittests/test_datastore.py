"""
unittests.test_datastore.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test datastore operations using mongmock client.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import IO
from zoneinfo import ZoneInfo

import mongomock
import pymongo
import pytest
from pydantic import ValidationError

from api import datastore
from models import weaver


def __from_ts(ts: str) -> datetime:
    """Convert timestamp with the format `2024-01-03 19:30:00` to specified timezone."""
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")


@pytest.fixture(autouse=True)
def _auto_mongomock_client_patch():
    """Mock the Mongo client. Remove at teardown."""
    datastore.GLOBAL.update(db_client=mongomock.MongoClient())
    yield
    datastore.GLOBAL.pop("db_client", None)


@pytest.fixture(autouse=True, scope="function")
def _auto_cleanup_database():
    db = mongomock.MongoClient().sounds
    for name in {
        datastore.METADATAS,
        datastore.USERS,
        datastore.PROMPTS,
        datastore.USERNAME_TO_ID,
        datastore.PROMPT_MANAGER,
    }:
        db.drop_collection(name)


def _db() -> mongomock.database.Database:
    """Get the test database."""
    return datastore.GLOBAL.get("db_client").sounds


def _voice_path(filename: str) -> str:
    """return the voice file path given the filename."""
    return str(datastore.VOICES_DIR / filename)


@pytest.fixture
def _mock_voices_directory(mocker):
    """Patch the voices directory to a temp file instead of disk."""
    old = datastore.VOICES_DIR
    tmpdir = tempfile.TemporaryDirectory()
    datastore.VOICES_DIR = Path(tmpdir.name)
    yield
    tmpdir.cleanup()
    datastore.VOICES_DIR = old

    # def test_shutdown():
    # there's a working client
    datastore.shutdown()
    # there's no working client
    datastore.shutdown()


def test_insert_voice_succeeds(mocker, _mock_voices_directory):
    metadata = weaver.VoiceMetadata(
        _id="honeybee",
        audio_extension="wav",
        datetime=__from_ts("2024-01-03 19:30:00"),
        username="fb/12345",
        prompt_id=2,
    )
    assert (
        datastore.insert_voice(
            audio_content=b"Buzz buzzzzz bizz zzzz ~",
            **dict(metadata),
        )
        == "honeybee"
    )

    # The new file is saved in temp dir with the correct content
    assert open(_voice_path("honeybee.wav"), "r").read() == "Buzz buzzzzz bizz zzzz ~"

    # The voice metadata is stored in database
    doc = _db().get_collection(datastore.METADATAS).find_one("honeybee")
    assert metadata == weaver.VoiceMetadata.model_validate(doc)


def test_insert_voice_file_save_fails(_mock_voices_directory):
    metadata = weaver.VoiceMetadata(
        _id="honeybee",
        audio_extension="wav",
        datetime=__from_ts("2024-01-03 19:30:00"),
        username="fb/12345",
        prompt_id=2,
    )
    # New file fails to save
    with pytest.raises(TypeError):
        datastore.insert_voice(audio_content="this isn't byte type", **dict(metadata))

    # File not found since the write is unsucessful
    with pytest.raises(FileNotFoundError):
        open(_voice_path("honeybee"), "r").read()

    # Metadata not found in database since transaction aborted
    assert _db().get_collection(datastore.METADATAS).find_one("honeybee") is None


def test_insert_voice_metadata_fails(_mock_voices_directory):
    # New file fails to save
    with pytest.raises(ValidationError):
        datastore.insert_voice(
            audio_content=b"Buzz buzzzzz bizz zzzz ~",
            id="honeybee",
            audio_extension="wav",
            datetime=__from_ts("2024-01-03 19:30:00"),
            username="fb/12345",
            prompt_id="j",
        )

    # File not found since the write since transaction aborted
    with pytest.raises(FileNotFoundError):
        open(_voice_path("honeybee"), "r").read()

    # Metadata not found in database since ValidationError
    assert _db().get_collection(datastore.METADATAS).find_one("honeybee") is None


def test_insert_user_successfully():
    user = weaver.User(
        _id="fb/12345",
        first_name="Bee",
        last_name="Honey",
        username="queen_bee_is_da_best",
    )

    assert datastore.insert_user(**(user.model_dump(exclude_unset=True))) == "fb/12345"

    # Users table contains document
    doc = _db().get_collection(datastore.USERS).find_one("fb/12345")
    assert weaver.User.model_validate(doc) == user

    # Username to id mapping contains the entry
    assert (
        _db()
        .get_collection(datastore.USERNAME_TO_ID)
        .find_one("queen_bee_is_da_best")["id"]
        == "fb/12345"
    )


def test_insert_user_fails_users():
    with pytest.raises(ValidationError):
        datastore.insert_user(
            id="fb/12345", first_name=234, username="queen_bee_is_da_best"
        )

    print(f"159: {datastore.USERS}")
    # Users table contains no document since failure
    assert _db().get_collection(datastore.USERS).find_one("fb/12345") is None

    # Username to id mapping contains the entry since trasanction aborts
    assert (
        _db().get_collection(datastore.USERNAME_TO_ID).find_one("queen_bee_is_da_best")
        is None
    )


@pytest.mark.xfail(reason="Needs data transaction manager for this to pass.")
def test_insert_user_fails_mapping():
    # change collection name to create some sort of error
    placeholder = datastore.USERNAME_TO_ID
    datastore.USERNAME_TO_ID = 98765

    with pytest.raises(TypeError):
        datastore.insert_user(
            id="fb/12345",
            first_name="Honey",
            last_name="Bee",
            username="queen_bee_is_da_best",
        )

    # Users table contains no document since trasanction aborts
    assert _db().get_collection(datastore.USERS).find_one("fb/12345") is None

    # Username to id mapping contains the entry since failure
    assert _db().get_collection(placeholder).find_one("queen_bee_is_da_best") is None

    # revert the collection name back
    datastore.USERNAME_TO_ID = placeholder


def test_insert_prompt_succeeds_first_prompt():
    kwargs = dict(
        text="what is your favorite flower?",
        begins=__from_ts("2024-01-04 00:00:00"),
        ends=__from_ts("2024-01-11 23:59:59"),
    )
    assert datastore.insert_prompt(**kwargs) == 0

    doc = _db().get_collection(datastore.PROMPTS).find_one(0)
    assert kwargs.items() <= doc.items()  # kwargs is subset aside from the id field


def test_insert_prompt_succeeds_second_prompt():
    kwargs = dict(
        text="Flower quality in Golden Gate Park vs. Central Park?",
        begins=__from_ts("2024-01-11 00:00:00"),
        ends=__from_ts("2024-01-18 23:59:59"),
    )

    assert (
        datastore.insert_prompt(
            text="what is your favorite flower?",
            begins=__from_ts("2024-01-04 00:00:00"),
            ends=__from_ts("2024-01-11 23:59:59"),
        )
        == 0
    )
    assert datastore.insert_prompt(**kwargs) == 1

    doc = _db().get_collection(datastore.PROMPTS).find_one(1)
    assert kwargs.items() <= doc.items()  # kwargs is subset aside from the id field


def test_new_db(mocker):
    datastore.shutdown()
    assert "db_client" not in datastore.GLOBAL

    mocker.patch("pymongo.MongoClient", return_value=mocker.Mock(specs=["server_info"]))
    datastore.__database()

    assert "db_client" in datastore.GLOBAL
