"""
api.utils.py
~~~~~~~~~~~~
Utilities used by api.
"""
# pylint: disable=logging-format-interpolation
# TODO: better name

import logging
import mimetypes
from collections.abc import Mapping
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests

from api import datastore
from models import facebook

LOGGER = logging.getLogger(__name__)


def handle_user_message(message: facebook.Message):
    """If the user message's attachments are audios, archive them."""
    if not dict(message).get("attachments"):
        raise AttributeError("user message doesn't have attachments")

    for i, attachment in enumerate(message.attachments):
        __extract_and_store_audio_from_url(
            attachment=attachment, key=f"{message.mid}--{i}"
        )


def extract_header_datetime(
    header: Mapping, timezone: str = "America/Los_Angeles"
) -> datetime:
    """Extract datetime Fri, 01 Jan 1999 00:00:00 GMT
    Args:
    header -- The http response header json
    timezone -- Optional - The timezone converting to. Default is America/Los_Angeles timezone.

    Returns:
    The converted datetime representing as a datetime. If header doesn't have a datetime, return now.
    """
    header_dt = header.get("date", None) or header.get("last-modified", None)

    # Trying to get the zoneinfo, if none found, reverted back to default tz in PST
    try:
        tz_info = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        tz_info = ZoneInfo("America/Los_Angeles")

    if header_dt:  # Format "Fri, 01 Jan 1999 00:00:00 GMT"
        return (
            datetime.strptime(header_dt, "%a, %d %b %Y %H:%M:%S %Z")
            .replace(tzinfo=ZoneInfo("UTC"))
            .astimezone(tz_info)
        )

    # If no header datetime found, get current time
    return datetime.now(tz=tz_info)


def extract_attachment_filename(header: Mapping) -> Optional[str]:
    """Extract the filename of the attachement, specifically in Content-Disposition. Return None if not found."""
    # According to https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition, Content-Disposition
    # syntax for attachment type is either `attachment; filename=<name>` or `attachment`. If the attachment doesn't
    # have filename, we will simply return None.
    name = header.get("Content-Disposition", "").strip("attachment; filename=")
    return name if name else None


def __extract_and_store_audio_from_url(
    attachment: facebook.Attachment, key: str
) -> str:
    """Download the audio from url to ./records and store its metadata to datastore's 'METADATAS table."""
    # Ensure that the attachment is an audio type and has a downloadable url
    if (
        not attachment.type == facebook.AttachmentType.AUDIO
        or not attachment.payload.url
    ):
        raise AttributeError("Attachment not an audio.")

    # Download the audio file
    try:
        response = requests.get(attachment.payload.url, stream=True)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.HTTPError(e)

    # Extract neccesary metadata for weaver.VoiceMetadata
    header = response.headers
    dt = extract_header_datetime(header)
    filename = extract_attachment_filename(header)
    filetype = mimetypes.guess_extension(header.get("Content-Type"))
    if not filetype:  # if we cannot guess the file type (extension), raise error
        raise AttributeError("Cannot detech the attachment's audio file extension.")

    # Save the static file to threads
    datastore.insert_sound(
        key=key,
        audio_content=response,
        dt=dt,
        title=filename,
        audio_extension=filetype.strip("."),
    )
