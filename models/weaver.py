"""
models.weaver.py
~~~~~~~~~~~~~~~~~~~~~~
Sound Weaving models
"""

import datetime
from typing import Optional, Sequence

from pydantic import BaseModel
from enum import Enum


class VoiceMetadata(BaseModel):
    key: str  # unreadable name stored in datastore
    datetime: datetime.datetime  # date and time archived
    audio_extension: str  # audio file type/extension
    username: str  # username of the sound's owner
    prompt_id: int  # prompt id of the sound


class User(BaseModel):
    username: str  # unique user id stored and display in the app
    first_name: str  # user's first name
    last_name: str  # user's last name
    voice_set: Sequence[str] = {}  # user's voice files
    prompt_set: Sequence[int]  = {}  # user's prompt participated


class Prompt(BaseModel):
    prompt_id: int  # unique id indicate the prompt
    begins: datetime.datetime  # prompt begin date
    ends: datetime.datetime  # prompt end date
    text: str  # question/prompt text
    voice_set: Sequence[str] = {}  # voice files responding to this prompt
    user_set: Sequence[str] = {}  # usernames responding to this prompt
