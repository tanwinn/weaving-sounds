"""
models.facebook.py
~~~~~~~~~~~~~~~~~~~~~~
Facebook Message models.
Based on Meta Developers Document
https://developers.facebook.com/docs/messenger-platform/reference/webhook-events
"""
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator


class AttachmentPayload(BaseModel):
    """Attachment's payload model"""

    url: str = None
    is_reusable: bool = None


class AttachmentType(Enum):
    """Attachment's type class"""

    AUDIO = "audio"
    IMAGE = "image"
    FILE = "file"
    VIDEO = "video"


class Attachment(BaseModel):
    """Message's attachement model"""

    type: AttachmentType
    payload: AttachmentPayload


class Message(BaseModel):
    """Message model"""

    mid: str
    text: str = None
    quick_reply: Mapping = None
    reply_to: Mapping = None
    attachments: Optional[Sequence[Attachment]] = None


class User(BaseModel):
    """User model"""

    id: Union[str, int]


class Messaging(BaseModel):
    """Messaging object"""

    sender: User
    recipient: User
    timestamp: int
    message: Message


class MessageEvent(BaseModel):
    """MessageEvent models in webhook event."""

    id: str
    time: int
    messaging: Sequence[Messaging]


class Event(BaseModel):
    """Webhook event model"""

    object: str = Field(examples=["page"])
    entry: Sequence[MessageEvent] = None

    @field_validator("object")
    @classmethod
    def object_must_be_page(cls, value):
        if value == "page":
            return value
        raise ValueError("object must be page")


""" 
Models based on Send API
https://developers.facebook.com/docs/messenger-platform/reference/send-api
"""


class ResponseMessage(BaseModel):
    """ResponseMessage of Response model"""

    text: str


class Response(BaseModel):
    """Chatbot's Response model back to the Facebook sending user"""

    message: ResponseMessage
    recipient: User
