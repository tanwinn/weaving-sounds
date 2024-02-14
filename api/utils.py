"""
api.utils.py
~~~~~~~~~~~~
Utilities used by api.
"""
# pylint: disable=logging-format-interpolation
# TODO: better name

import logging
import mimetypes
import os
from collections.abc import Mapping
from datetime import datetime
from typing import Optional, Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests

from api import datastore
from models import exceptions, facebook

LOGGER = logging.getLogger(__name__)
FB_PAGE_TOKEN = os.environ.get("FB_PAGE_TOKEN", "default")
FB_GRAPH_API = "https://graph.facebook.com/v19.0"


def handle_fb_user(sender_id: Union[str, int]) -> str:
    """Get the user's Facebook identity"""
    user_id = f"fb/{sender_id}"
    # if user not registered, get user basic info and register to the system
    if datastore.get_user_by_id(user_id) is None:
        LOGGER.info("User not found in the system! Registering new user...")
        try:
            # According to Meta's doc: https://developers.facebook.com/docs/messenger-platform/identity/user-profile/#available-profile-fields
            response = requests.get(
                f"{FB_GRAPH_API}/{sender_id}?access_token={FB_PAGE_TOKEN}"
            )
            response.raise_for_status()
            response = response.json()
            datastore.insert_user(
                user_id,
                first_name=response.get("first_name", "undefined"),
                last_name=response.get("last_name", None),
            )
            reply_to(
                sender_id,
                f"New user detected. Registered user with ID {user_id} on webiste. To change your displayable username, go to tanwinn.io/weaving-sounds :)",
            )
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.HTTPError(e)
    return user_id


def handle_user_message(user_id: str, message: facebook.Message):
    """If the user message's attachments are audios, archive them."""
    if not dict(message).get("attachments"):
        raise exceptions.InputError("User message doesn't have attachments.")

    if len(message.attachments) > 1:
        raise exceptions.InputError(
            "Too many attachements at once. Please upload one at a time."
        )

    __extract_and_store_audio_from_url(
        user_id=user_id, attachment=message.attachments[0], voice_id=f"{message.mid}"
    )
    LOGGER.info(f"Saved audio & metadata: {message.mid}")
    return f"Saved audio file with ID {message.mid}"


def reply_to(user_id: str, text: str) -> Mapping:
    """
    Compose a message/reply to `user_id` with content of `text`
    and send it to Messenger through POST call to FB_GRAPH_API
    """
    data = facebook.Response(
        recipient=facebook.User(id=user_id),
        message=facebook.ResponseMessage(text=text),
    ).model_dump()
    LOGGER.info(f"Prepping call to Facebook Graph API.")
    response = requests.post(
        f"{FB_GRAPH_API}/me/messages?access_token={FB_PAGE_TOKEN}", json=data
    )
    response.raise_for_status()
    return data


def __extract_header_datetime(header: Mapping) -> datetime:
    """Extract datetime Fri, 01 Jan 1999 00:00:00 GMT
    Args:
    header -- The http response header json

    Returns:
    The datetime object in UTC. If header doesn't have a datetime, return now.
    """
    header_dt = header.get("date", None) or header.get("last-modified", None)

    if header_dt:  # Format "Fri, 01 Jan 1999 00:00:00 GMT"
        return datetime.strptime(header_dt, "%a, %d %b %Y %H:%M:%S %Z").replace(
            tzinfo=ZoneInfo("UTC")
        )

    # If no header datetime found, get current time
    return datetime.now(tz=ZoneInfo("UTC"))


def utc_to_(dt: datetime, timezone: str = "America/Los_Angeles") -> datetime:
    """Converted datetime in UTC to specified timezone."""
    # Trying to get the zoneinfo, if none found, reverted back to default tz in PST
    try:
        tz_info = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        tz_info = ZoneInfo("America/Los_Angeles")

    return dt.astimezone(tz_info)


def datetime_from_ts(ts: str, timezone: str = "UTC") -> datetime:
    """Convert timestamp with timezone to datetime object"""
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo(timezone))


def __extract_attachment_filename(header: Mapping) -> Optional[str]:
    """Extract the filename of the attachement, specifically in Content-Disposition. Return None if not found."""
    # According to https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition, Content-Disposition
    # syntax for attachment type is either `attachment; filename=<name>` or `attachment`. If the attachment doesn't
    # have filename, we will simply return None.
    name = header.get("Content-Disposition", "").strip("attachment; filename=")
    return name if name else None


def __extract_and_store_audio_from_url(
    user_id: str, attachment: facebook.Attachment, voice_id: str
) -> str:
    """Download the audio from url to ./records and store its metadata to datastore's 'METADATAS table."""
    # Ensure that the attachment is an audio type and has a downloadable url
    if (
        not attachment.type == facebook.AttachmentType.AUDIO
        or not attachment.payload.url
    ):
        raise exceptions.InputError("Attachment not an audio.")

    # Download the audio file
    try:
        response = requests.get(attachment.payload.url, stream=True)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.HTTPError(e)

    # Extract neccesary metadata for weaver.VoiceMetadata
    header = response.headers
    dt = __extract_header_datetime(header)
    filename = __extract_attachment_filename(header)
    filetype = mimetypes.guess_extension(header.get("Content-Type"))
    if not filetype:  # if we cannot guess the file type (extension), raise error
        raise exceptions.InputError(
            "Cannot detect the attachment's audio file extension."
        )

    # Save the static file to voices
    datastore.insert_voice(
        id=voice_id,
        audio_content=response.content,
        datetime=dt,
        audio_extension=filetype.strip("."),
        prompt_id=1,  # todo:
        username=user_id,
    )
