"""
models.weaver.py
~~~~~~~~~~~~~~~~~~~~~~
Sound Weaving models
"""

from collections.abc import Sequence, Set
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class VoiceMetadata(BaseModel):
    """Metadata for the voice record stored in voices dir."""

    id: str = Field(alias="_id")  # unreadable index in datastore
    datetime: datetime  # date and time archived
    audio_extension: str  # audio file type/extension
    username: str  # username of the sound's owner
    prompt_id: int  # prompt id of the sound


class User(BaseModel):
    """Users of the website. Owners of the voice records.
    Can be from multiple platforms, for now only serves FB messenger."""

    id: str = Field(
        alias="_id"
    )  # unique id stored. Format: <platform>/<id> ==> fb/7123882112
    username: str  # unique & displayable user id on the website
    first_name: str  # user's first name
    last_name: Optional[str] = None  # user's last name
    voice_set: Set[str] = set()  # user's voice files
    prompt_set: Set[int] = set()  # user's prompt participated


class Prompt(BaseModel):
    """The prompt is a question answered by user in the form of voice record."""

    id: int = Field(
        alias="_id"
    )  # unique id indicate the prompt. Number in order of the prompt.
    begins: datetime  # prompt begin date
    ends: datetime  # prompt end date
    text: str  # question/prompt text
    voice_set: Sequence[str] = {}  # voice files responding to this prompt
    user_set: Sequence[str] = {}  # usernames responding to this prompt


class UsernameToId(BaseModel):
    username: str = Field(alias="_id")  # Unique displayable & user-friendly identity
    id: str  # internal id


class PromptManager(BaseModel):
    id: str = Field(alias="_id", default="manager")
    active_prompt: Optional[int] = None
    next_index: int = 0  # next index avalaible for prompt counter
    deleted_prompts: Set[int] = set()  # archived/deleted index


class VoiceMetadataUpdate(BaseModel):
    """Metadata update model"""

    datetime: Optional[datetime] = None  # date and time archived
    audio_extension: Optional[str] = None  # audio file type/extension
    username: Optional[str] = None  # username of the sound's owner
    prompt_id: Optional[int] = None  # prompt id of the sound


class UserUpdate(BaseModel):
    """User Update model"""

    username: Optional[str] = None  # unique & displayable user id on the website
    first_name: Optional[str] = None  # user's first name
    last_name: Optional[str] = None  # user's last name
    voice_set: Optional[Sequence[str]] = None  # user's voice files
    prompt_set: Optional[Sequence[int]] = None  # user's prompt participated


class PromptUpdate(BaseModel):
    """Prompt update model"""

    begins: Optional[datetime] = None  # prompt begin date
    ends: Optional[datetime] = None  # prompt end date
    text: Optional[str] = None  # question/prompt text
    voice_set: Optional[Sequence[str]] = None  # voice files responding to this prompt
    user_set: Optional[Sequence[str]] = None  # usernames responding to this prompt


class UsernameToIdUpdate(BaseModel):
    """UsernameToId Update model"""

    id: Optional[str] = None  # internal id


class PromptManagerUpdate(BaseModel):
    """Prompt manager update model"""

    active_prompt: Optional[int] = None
    next_index: Optional[int] = None  # next index avalaible for prompt counter
    deleted_prompts: Optional[Set[int]] = None  # archived/deleted index
