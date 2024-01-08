"""
api.utils.py
~~~~~~~~~~~~
Utilities used by api.
"""
# pylint: disable=logging-format-interpolation
# TODO: better name

import logging
from collections.abc import Mapping
from datetime import datetime
from mimetypes import guess_extension
from typing import Optional

import pytz
import requests

from api import datastore
from models import facebook

LOGGER = logging.getLogger(__name__)


def handle_user_message(message: facebook.Message):
    """If the user message's attachments are audios, archive them."""
    try:
        for i, attachment in enumerate(message.attachments):
            # LOGGER.warning(f"type:{attachment.type};\nURL:{attachment.payload.url}")
            __extract_and_store_audio_from_url(
                attachment=attachment, key=f"{message.mid}--{i}"
            )
    except AttributeError:  # message does not have attachments
        return


def __extract_header_datetime(
    header: Mapping, timezone: datetime.tzinfo = pytz.timezone("America/Los_Angeles")
) -> datetime:
    """Extract datetime Fri, 01 Jan 1999 00:00:00 GMT
    Args:
    header -- The http response header json
    timezone -- Optional - The timezone converting to. Default is America/Los_Angeles timezone.

    Returns:
    The converted datetime representing as a datetime. If header doesn't have a datetime, return now.
    """
    header_dt = (
        header.get("Date", None)
        or header.get("Last-Modified", None)
        or datetime.now(tzinfo=pytz.utc)
    )
    return (  # Format "Fri, 01 Jan 1999 00:00:00 GMT"
        datetime.strptime(header_dt, "%a, %d %b %Y %H:%M:%S %Z")
        .replace(tzinfo=pytz.utc)  # http header datetime timezone is UTC.
        .astimezone(timezone)
    )


def __extract_attachment_filename(header: Mapping) -> Optional[str]:
    """Extract the filename of the attachement, specifically in Content-Disposition. Return None if not found."""
    # According to https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition, Content-Disposition
    # syntax for attachment type is either `attachment; filename=<name>` or `attachment`. If the attachment doesn't
    # have filename, we will simply return None.
    name = header.get("Content-Disposition").strip("attachment; filename=")
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
    response = requests.get(attachment.payload.url, stream=True)

    # Extract neccesary metadata for weaver.SoundThreadMetadata
    header = response.headers
    dt = __extract_header_datetime(header)
    filename = __extract_attachment_filename(header)
    filetype = guess_extension(header.get("Content-Type"))
    LOGGER.warning(f"GUESSTYPE: {filetype}")
    if not filetype:  # if we cannot guess the file type (extension), raise error
        raise AttributeError("Cannot detech the attachment's audio file extension.")

    # Save the static file to threads
    datastore.insert_thread(
        key=key,
        audio_content=response,
        dt=dt,
        title=filename,
        audio_type=filetype.strip("."),
    )
