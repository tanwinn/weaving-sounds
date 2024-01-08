"""
models.weaver.py
~~~~~~~~~~~~~~~~~~~~~~
Sound Weaving models
"""

import datetime
from typing import Optional

from pydantic import BaseModel


class SoundThreadMetadata(BaseModel):
    key: str  # unreadable name stored in datastore
    title: Optional[str] = None  # audio name defined by storer
    summary: Optional[str] = None  # summary of the sound
    datetime: datetime.datetime  # date and time archived
    audio_type: str  # audio file type/extension
