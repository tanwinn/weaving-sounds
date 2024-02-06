"""
api.datastore.py
~~~~~~~~~~~~~~~~
Database storage related CRUD operations.
TODO: set up actual database lol
"""
import sqlite3
import csv
import datetime
import logging
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
            key = row.get("key")
            metadata = weaver.VoiceMetadata.model_validate(row)
            _METADATAS[key] = metadata
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
    key: str,
    audio_content: any,
    audio_extension: str,
    dt: datetime.datetime,
    title: Optional[str] = None,
) -> str:
    """Save the audio file (sound thread) to threads directory. Insert the metadata to the datastore.
    Args:
    key -- the audio index key used as the unique identifier for the static file stored in threads & metadata table.
    audio_content -- the downloaded audio content
    audio_extension -- the downloaded audio file extension
    dt -- datetime of the audio content
    title -- optional. Human-readable title set by users.

    Returns:
    A key representing the filename stored in threads and index od the metadata in datastore.
    """

    # Save the static
    with open(str(THREADS_DIR / f"{key}.{audio_extension}"), "wb") as file:
        for chunk in audio_content.iter_content(chunk_size=10 * 1024):
            file.write(chunk)
    upsert_metadata(
        weaver.VoiceMetadata(
            key=key, title=title, audio_extension=audio_extension, datetime=dt
        )
    )


def delete_sound(key: str):
    """Delete the audio file and its metadata"""


def get_sound(key: str):
    """Get the audio file by key index"""


def upsert_metadata(metadata: weaver.VoiceMetadata):
    """Insert/Update the metadatas of a sound thread to in-memory"""
    _METADATAS[metadata.key] = metadata


def get_metadata(key: str):
    """Get metadata by key index"""


def get_keys_by_title(title: str) -> Sequence[str]:
    """Get the key index by titles. Since titles can be duplicated, there can be multiple keys mapped to the same title."""
