"""
api.datastore.py
~~~~~~~~~~~~~~~~
Database storage related CRUD operations.
TODO: set up actual database lol
"""
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


def insert_voice(
    id: str,
    audio_extension: str,
    audio_content: any,
    dt: datetime.datetime,
    user_id: str,
    prompt_id: int,
) -> str:
    """Save the audio file (sound thread) to threads directory. Insert the metadata to the datastore.
    Args:
    id -- the audio index _id used as the unique identifier for the static file stored in threads & metadata table.
    audio_extension -- the downloaded audio file extension
    audio_content -- the downloaded audio content
    dt -- datetime of the audio content
    username -- owner of the voice record
    prompt_id -- prompt associates with the voice record

    Returns:
    A voice_id representing the filename stored in threads and index id the metadata in datastore.
    """

    # Save the static
    with open(str(THREADS_DIR / f"{id}.{audio_extension}"), "wb") as file:
        for chunk in audio_content.iter_content(chunk_size=10 * 1024):
            file.write(chunk)
    __insert_metadata(
        weaver.VoiceMetadata(
            _id=id,
            audio_extension=audio_extension,
            datetime=dt,
            username=user_id,
            prompt_id=prompt_id,
        )
    )


def delete_voice(id: str):
    """Delete the voice file and its metadata"""


def get_voice(id: str) -> Optional[any]:
    """Get the voice file by id index. Return None if not found."""
    return None


def get_voices_by_prompt(id: str) -> Sequence[any]:
    """Get voice records by the id"""
    return []


def get_voices_by_user(id: str) -> Sequence[any]:
    """Get voice records by the id"""
    return []


def __insert_metadata(metadata: weaver.VoiceMetadata):
    """Insert the metadata. Must be done through voice insertion."""
    print(f"Inserted {metadata}")


def update_metadata(metadata: weaver.VoiceMetadata):
    """Update metadata. Indexed by id."""


def get_metadata(id: str) -> Optional[weaver.VoiceMetadata]:
    """Get metadata by id index. Return None if not found."""
    return None


def __delete_metadata():
    """Delete metadata. Must be done through voice deletion."""


def insert_user(id: str, first_name: str, last_name: Optional[str] = None) -> str:
    """Insert new user to the table"""
    print("Inserting User...")
    print(
        weaver.User(
            _id=id,
            username=id,
            first_name=first_name,
            last_name=last_name,
        )
    )
    return id


def get_user_by_id(id: str) -> Optional[weaver.User]:
    """Get the user by unique id (internal)."""
    return None


def get_user_id_by_username(username: str) -> str:
    """Get the id by unique username (user-friendly)."""
    # Store a mapping username -> id
    return None


def get_user_by_username(username: str) -> Optional[weaver.User]:
    """Get the user by unqiue username (user-friendly)."""


def update_user(user: weaver.User):
    """Update user. Indexed by id."""


def __update_username(id: str, username: str):
    """Update username. And the mapping username->id."""


def delete_user(id: str):
    """Delete user by id."""


def __delete_username(user_name: str):
    """Delete the username in the mapping since user is deleted."""
