"""
api.datastore.py
~~~~~~~~~~~~~~~~
Database storage related CRUD operations.
TODO: set up actual database lol
"""
import csv
import datetime
import logging
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from models import weaver

LOGGER = logging.getLogger(__name__)

ROOT = Path(__file__).joinpath("..").joinpath("..").resolve()
THREADS_DIR = ROOT / "threads"
THREAD_METADATAS_FILE = THREADS_DIR / "metadatas.csv"
_METADATAS = {}


def load_memory_from_storage():
    """Load the metadata tables from storage (metadatas.csv file) to in-memory api.datastore.METADATAS_ - for app startup."""
    with open(THREAD_METADATAS_FILE, "r") as rfile:
        csv_dict_reader = csv.DictReader(rfile, delimiter=",")

        for row in csv_dict_reader:
            voice_id = row.get("voice_id")
            metadata = weaver.VoiceMetadata.model_validate(row)
            _METADATAS[voice_id] = metadata
    LOGGER.warning(f"Successfully loaded memory from storage. Metadatas:\n{_METADATAS}")


def load_storage_from_memory():
    """Update the storage (metadatas.csv file) from in-memory api.datastore.METADATAS_ - for app teardown."""
    with open(THREAD_METADATAS_FILE, "w") as wfile:
        writer = csv.DictWriter(
            wfile, fieldnames=weaver.VoiceMetadata.__fields__.keys()
        )
        writer.writeheader()

        for data in _METADATAS.values():
            writer.writerow(dict(data))
    LOGGER.warning(f"Successfully loaded storage from memory.")


def insert_sound(
    voice_id: str,
    audio_extension: str,
    audio_content: any,
    dt: datetime.datetime,
    user_id: str,
    prompt_id: int,
) -> str:
    """Save the audio file (sound thread) to threads directory. Insert the metadata to the datastore.
    Args:
    voice_id -- the audio index voice_id used as the unique identifier for the static file stored in threads & metadata table.
    audio_extension -- the downloaded audio file extension
    audio_content -- the downloaded audio content
    dt -- datetime of the audio content
    username -- owner of the voice record
    prompt_id -- prompt associates with the voice record

    Returns:
    A voice_id representing the filename stored in threads and index id the metadata in datastore.
    """

    # Save the static
    with open(str(THREADS_DIR / f"{voice_id}.{audio_extension}"), "wb") as file:
        for chunk in audio_content.iter_content(chunk_size=10 * 1024):
            file.write(chunk)
    upsert_metadata(
        weaver.VoiceMetadata(
            voice_id=voice_id,
            audio_extension=audio_extension,
            datetime=dt,
            username=user_id,
            prompt_id=prompt_id,
        )
    )


def delete_sound(voice_id: str):
    """Delete the audio file and its metadata"""


def get_sound(voice_id: str):
    """Get the audio file by voice_id index"""


def upsert_metadata(metadata: weaver.VoiceMetadata):
    """Insert/Update the metadatas of a sound thread to in-memory"""
    _METADATAS[metadata.voice_id] = metadata


def get_metadata(voice_id: str):
    """Get metadata by voice_id index"""


def get_keys_by_title(title: str) -> Sequence[str]:
    """Get the voice_id index by titles. Since titles can be duplicated, there can be multiple keys mapped to the same title."""


def get_user(id: str) -> Optional[weaver.User]:
    """Get the user by id"""
    return None


def insert_user(user_id: str, first_name: str, last_name: Optional[str] = None) -> str:
    """Insert new user to the table"""
    print("Inserting User...")
    print(
        weaver.User(
            user_id=user_id,
            username=user_id,
            first_name=first_name,
            last_name=last_name,
        )
    )
    return user_id
