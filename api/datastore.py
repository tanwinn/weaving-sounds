"""
api.datastore.py
~~~~~~~~~~~~~~~~
Database storage related CRUD operations.
TODO: set up actual database lol
"""
import csv
import datetime
import logging
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Optional, Union
from zoneinfo import ZoneInfo

import pymongo
import transaction
from pydantic import BaseModel as PydanticModel

from models import weaver

LOGGER = logging.getLogger(__name__)

# Voice records related config

ROOT = Path(__file__).joinpath("..").joinpath("..").resolve()
VOICES_DIR = ROOT / "voices"

# MongoDB related config

METADATAS = "voice_metadata"
USERS = "users"
PROMPTS = "prompts"
USERNAME_TO_ID = "username_to_id"
PROMPT_MANAGER = "prompt_manager"

GLOBAL = {}
MONGO_CONN_STR = os.environ.get("MONGO_CONN_STR", "mongodb://127.0.0.1:27017")


def __database() -> pymongo.database.Database:
    """Get the `sounds` database"""
    if "db_client" not in GLOBAL:
        LOGGER.info("No mongo client found. Creating a new one...")
        startup()
    return GLOBAL.get("db_client").sounds


def startup():
    """Startup the mongo client"""
    LOGGER.info("Initializing the mongo client connection")
    client = pymongo.MongoClient(
        host=MONGO_CONN_STR, connectTimeoutMS=3000, serverSelectionTimeoutMS=3500
    )
    client.server_info()  # check server liveness
    GLOBAL.update(db_client=client)


def shutdown():
    """Shut down the mongo client"""
    LOGGER.info("Closing mongo client connection")
    client = GLOBAL.pop("db_client", None)
    if client:
        client.close()


def __insert_collection(collection_name: str, document: PydanticModel) -> str:
    """Insert one document to the collection"""

    collection = __database().get_collection(collection_name)
    inserted = collection.insert_one(
        document.model_dump(by_alias=True, exclude_unset=True)
    ).inserted_id
    LOGGER.info(f"Inserted document with id {inserted} to {collection_name}")

    return inserted


def __get_document(collection_name: str, query: Mapping = None) -> PydanticModel:
    """Get documents from given collection"""
    LOGGER.info(f"Getting document in {collection_name} " f"with query={query}")
    collection = __database().get_collection(collection_name)
    return collection.find_one(query)


def __get_documents(
    collection_name: str, query: Union[str, Mapping] = None
) -> Sequence[PydanticModel]:
    """Get documents from given collection"""
    LOGGER.info(
        f"Getting multiple documents in {collection_name} " f"with query={query}"
    )
    collection = __database().get_collection(collection_name)
    return collection.find(query)


def __update_collection(
    collection_name: str, query: Union[str, Mapping], doc: PydanticModel
) -> any:
    """Update the collection given the collection_name, doc, and filter_dict"""
    LOGGER.info(f"Updating documents to {collection_name}")
    collection = __database().get_collection(collection_name)
    return collection.find_one_and_update(
        ({"_id": query} if isinstance(query, str) else query),
        {"$set": doc.model_dump(exclude_unset=True)},
    )


def insert_voice(
    id: str,
    audio_extension: str,
    audio_content: any,
    datetime: datetime.datetime,
    username: str,
    prompt_id: int,
) -> str:
    """Save the audio file (voice records) to voices directory. Insert the metadata to the datastore.
    Args:
    id -- the audio index _id used as the unique identifier for the static file stored in voices & metadata table.
    audio_extension -- the downloaded audio file extension
    audio_content -- the downloaded audio content
    datetime -- datetime of the audio content
    username -- owner of the voice record
    prompt_id -- prompt associates with the voice record

    Returns:
    A voice_id representing the filename stored in voices and index id the metadata in datastore.
    """
    try:
        # Save the static
        path = str(VOICES_DIR / f"{id}.{audio_extension}")
        with open(path, "wb") as file:
            file.write(audio_content)
        metadata_id = __insert_collection(
            METADATAS,
            weaver.VoiceMetadata(
                _id=id,
                datetime=datetime,
                audio_extension=audio_extension,
                username=username,
                prompt_id=prompt_id,
            ),
        )
        return metadata_id
    except Exception as e:
        LOGGER.warning(f"Aborting transaction: {e}")
        transaction.abort()
        raise e


def delete_voice(id: str):
    """Delete the voice file and its metadata"""


def get_voice(id: str) -> Optional[any]:
    """Get the voice file by id index. Return None if not found."""


def get_voices_by_prompt(id: str) -> Sequence[any]:
    """Get voice records by the id"""


def get_voices_by_user(id: str) -> Sequence[any]:
    """Get voice records by the id"""


def update_metadata(metadata: weaver.VoiceMetadata):
    """Update metadata. Indexed by id."""


def get_metadata(id: str) -> Optional[weaver.VoiceMetadata]:
    """Get the metadata by id index. Return None if not found."""
    doc = __get_document(MEADATA, query=id)
    if doc:
        doc = weaver.VoiceMetadata.model_validate(doc)
    return doc


def __delete_metadata():
    """Delete metadata. Must be done through voice deletion."""


def insert_user(
    id: str,
    first_name: str,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
) -> str:
    """Insert new user to the table"""
    # todo: use mongodb transaction
    # Add user to the Users collection
    inserted = __insert_collection(
        USERS,
        weaver.User(
            _id=id,
            username=username or id,
            first_name=first_name,
            last_name=last_name,
        ),
    )
    # Add username to id mapping
    __insert_collection(
        USERNAME_TO_ID, weaver.UsernameToId(_id=(username or id), id=id)
    )
    return inserted


def get_user_by_id(id: str) -> Optional[weaver.User]:
    """Get the user by unique id (internal)."""
    doc = __get_document(USERS, query=id)
    if doc:
        doc = weaver.User.model_validate(doc)
    return doc


def get_user_by_username(username: str) -> Optional[weaver.User]:
    """Get the user by unqiue username (user-friendly)."""
    # Store a mapping username -> id
    user_id = __get_document(USERNAME_TO_ID, query=username)
    return get_user_by_id(user_id)


def update_user(user: weaver.User):
    """Update user. Indexed by id."""


def __update_username(id: str, username: str):
    """Update username. And the mapping username->id."""


def delete_user(id: str):
    """Delete user by id."""


def __delete_username(user_name: str):
    """Delete the username in the mapping since user is deleted."""


def insert_prompt(text: str, begins: datetime.datetime, ends: datetime.datetime):
    """Insert prompt."""
    # todo: use mongo transaction
    # get the prompt manager
    manager = __get_or_create_prompt_manager()
    inserted = __insert_collection(
        PROMPTS,
        weaver.Prompt(_id=manager.next_index, begins=begins, ends=ends, text=text),
    )

    # update prompt manager
    __update_collection(
        PROMPT_MANAGER,
        query="manager",
        doc=weaver.PromptManagerUpdate(next_index=manager.next_index + 1),
    )
    return inserted


def update_prompt(prompt: weaver.Prompt):
    """Update prompt."""


def __get_or_create_prompt_manager() -> weaver.PromptManager:
    """get an existing or create new prompt manager"""
    doc = __get_document(PROMPT_MANAGER, query="manager")
    if not doc:
        doc = weaver.PromptManager(_id="manager")
        __insert_collection(PROMPT_MANAGER, doc)
    else:
        doc = weaver.PromptManager.model_validate(doc)
    return doc
