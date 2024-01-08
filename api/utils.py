"""
api.utils.py
~~~~~~~~~~~~
Utilities used by api.
"""
# pylint: disable=logging-format-interpolation
# TODO: better name

import logging
from pprint import pformat as pf
from pathlib import Path
from collections.abc import Mapping

import requests

from models import facebook
from datetime import datetime
import pytz

LOGGER = logging.getLogger(__name__)


def handle_user_message(message: facebook.Message):
    """If the user message's attachments are audios, archive them."""
    try:
        for attachment in message.attachments:
            LOGGER.warning(f"type:{attachment.type};\nURL:{attachment.payload.url}")
            __extract_and_store_thread_from_url(attachment)
    except AttributeError:  # message does not have attachments
        return


def __extract_header_datetime(header: Mapping, timezone: datetime.tzinfo) -> datetime:
    """Extract datetime Fri, 01 Jan 1999 00:00:00 GMT from a http response header json to a specificed timezone."""
    header_dt = (
        header.get("Date", None)
        or header.get("Last-Modified", None)
        or datetime.now(tzinfo=pytz.utc)
    )
    return (  # Format "Fri, 01 Jan 1999 00:00:00 GMT"
        datetime.strptime(header_dt, "%a, %d %b %Y %H:%M:%S %Z")
        .replace(tzinfo=pytz.utc)
        .astimezone(timezone)
    )


def __extract_and_store_thread_from_url(attachment: facebook.Attachment):
    """Download the audio from url to ./records and store a metadata row to datastore.METADATAS"""
    if attachment.type == facebook.AttachmentType.AUDIO and attachment.payload.url:
        LOGGER.warning("AUDIO!!!!!")
        with requests.get(attachment.payload.url, stream=True) as response:
            header = response.headers
            LOGGER.warning(pf(header))
            dt = __extract_header_datetime(header, pytz.timezone("America/Los_Angeles"))
            LOGGER.warning(f"datetime converted: {dt}")
