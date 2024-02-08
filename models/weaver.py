"""
models.weaver.py
~~~~~~~~~~~~~~~~~~~~~~
Sound Weaving models
"""

import datetime
from enum import Enum
from typing import Optional, Sequence

from pydantic import BaseModel, Field


class VoiceMetadata(BaseModel):
    """Metadata for the voice record stored in threads dir."""

    id: str = Field(alias="_id")  # unreadable index in datastore
    datetime: datetime.datetime  # date and time archived
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
    voice_set: Sequence[str] = {}  # user's voice files
    prompt_set: Sequence[int] = {}  # user's prompt participated


class Prompt(BaseModel):
    """The prompt is a question answered by user in the form of voice record."""

    id: int = Field(
        alias="_id"
    )  # unique id indicate the prompt. Number in order of the prompt.
    begins: datetime.datetime  # prompt begin date
    ends: datetime.datetime  # prompt end date
    text: str  # question/prompt text
    voice_set: Sequence[str] = {}  # voice files responding to this prompt
    user_set: Sequence[str] = {}  # usernames responding to this prompt
