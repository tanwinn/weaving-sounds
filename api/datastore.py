"""
api.datastore.py
~~~~~~~~~~~~~~~~
Database storage related CRUD operations.
TODO: set up actual database lol
"""
import csv
import logging
from pathlib import Path

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
            metadata = weaver.SoundThreadMetadata.model_validate(row)
            _METADATAS[key] = metadata
    LOGGER.warning(f"Successfully loaded memory from storage. Metadatas:\n{_METADATAS}")


def load_storage_from_memory():
    """Update the storage (metadatas.csv file) from in-memory api.datastore.METADATAS_ - for app teardown."""
    with open(THREAD_METADATAS_FILE, "w") as wfile:
        writer = csv.DictWriter(
            wfile, fieldnames=["key", "title", "summary", "date", "time"]
        )
        writer.writeheader()

        for data in _METADATAS.values():
            writer.writerow(dict(data))
    LOGGER.warning(f"Successfully loaded storage from memory.")

def insert_thread(key:str, audio_file: any):
    """Insert the audio file to threads directory"""

def delete_thread(key: str):
    """Delete the audio file and its metadata"""

def get_thread(key: str):
    """Get the audio file by key"""

def upsert_metadata(metadata: weaver.SoundThreadMetadata):
    """Insert/Update the metadatas of a sound thread to in-memory"""

def get_metadata(key: str = None, title: str = None):
    """Get metadata by audio key or metadata title."""
    if key or title:
        pass
    raise AttributeError("Insufficient params: needs either thread key or title.")
