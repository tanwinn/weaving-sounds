"""
unittests.test_utils.py
~~~~~~~~~~~~~~~~~~~~~~~
Unittest for api.utils models
"""
from collections.abc import Mapping
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
import requests

from api import datastore, utils
from models import facebook


def __from_ts(ts: str, timezone: str) -> datetime:
    """Convert timestamp with the format `2024-01-03 19:30:00` to specified timezone."""
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo(timezone))


def __make_header(header_data: Mapping) -> requests.structures.CaseInsensitiveDict:
    """Convert a normal dictionary to case-insenstive http header similar to real object passed."""
    return requests.structures.CaseInsensitiveDict(header_data)


@pytest.mark.parametrize(
    "header_data,expected_ts",
    [
        ({"Date": "Thu, 04 Jan 2024 03:30:00 GMT"}, "2024-01-03 19:30:00"),
        ({"last-modified": "Thu, 04 Jan 2024 16:00:00 GMT"}, "2024-01-04 08:00:00"),
    ],
)
def test_extract_header_datetime_default_tz(header_data: Mapping, expected_ts: str):
    header = __make_header(header_data)
    expected = __from_ts(expected_ts, "America/Los_Angeles")
    assert utils.extract_header_datetime(header) == expected


def test_extract_header_datetime_different_tz():
    header = __make_header({"date": "Thu, 04 Jan 2024 03:30:00 GMT"})
    assert utils.extract_header_datetime(header, "America/New_York") == __from_ts(
        "2024-01-03 22:30:00", "America/New_York"
    )


def test_extract_header_datetime_invalid_header():
    header = __make_header({"header_no_date": "delilmama"})
    # Expecting now time, return without problem and with a timezone
    now = utils.extract_header_datetime(header, "America/Los_Angeles")
    assert now.tzinfo.key == "America/Los_Angeles"


def test_extract_header_datetime_invalid_timezone():
    header = __make_header({"Date": "Thu, 04 Jan 2024 03:30:00 GMT"})
    # Timezone input string is invalid, so revert back to default timezone PST
    assert utils.extract_header_datetime(header, "invalid/timezone") == __from_ts(
        "2024-01-03 19:30:00", "America/Los_Angeles"
    )


@pytest.mark.parametrize(
    "header_data",
    [
        {"content-disposition": "inline"},
        {"content-disposition": "attachment"},
        {"content-disposition": "attachment; filename="},
        {"content-type": "audio/wav"},
    ],
)
def test_extract_attachment_filename_not_found(header_data: Mapping):
    assert utils.extract_attachment_filename(__make_header(header_data)) is None


def test_extract_attachment_file_name_valid():
    header = __make_header({"Content-Disposition": "attachment; filename=oatmilk.wav"})
    utils.extract_attachment_filename(header) == "oatmilk.wav"


@pytest.mark.parametrize(
    "msg_data",
    [
        {"mid": "tinh-iu-vi-mo"},
        {
            "mid": "rainy-days",
            "text": "udon tempura chilly sauce",
            "attachments": [{"type": "video", "payload": {"url": "https://foo.bar"}}],
        },
        {
            "mid": "sunday-lunch",
            "text": "oyakodon",
            "attachments": [{"type": "audio", "payload": {}}],
        },
        {
            "mid": "monday-night",
            "text": "omurice",
        },
    ],
)
def test_handle_user_message_attribute_error(msg_data, mocker):
    # Mock external deps
    mocker.patch("api.datastore.insert_thread")
    invalid_msg = facebook.Message.model_validate(msg_data)
    with pytest.raises(AttributeError):
        utils.handle_user_message(invalid_msg)


def test_handle_user_message_http_error(mocker):
    mocker.patch("api.datastore.insert_thread")
    mocker.patch("requests.get", side_effect=requests.exceptions.ConnectionError())
    message = facebook.Message(
        mid="rainy-days",
        attachments=[
            facebook.Attachment(
                type="audio",
                payload=facebook.AttachmentPayload(url="invalid-url"),
            )
        ],
    )

    with pytest.raises(requests.exceptions.HTTPError):
        utils.handle_user_message(message)


def test_handle_user_message_filetype_unknown(mocker):
    # Mock external deps
    mocker.patch("api.datastore.insert_thread")
    mocker.patch(
        "requests.get",
        return_value=mocker.Mock(
            headers=__make_header(
                {
                    "Date": "Thu, 04 Jan 2024 03:30:00 GMT",
                    "Content-Type": "audio/gibberishhs",
                    "Content-Disposition": "attachment; filename=oatmilk",
                }
            ),
            status_code=200,
        ),
    )
    with pytest.raises(AttributeError):
        message = facebook.Message(
            mid="rainy-days",
            attachments=[
                facebook.Attachment(
                    type="audio",
                    payload=facebook.AttachmentPayload(url="tanwinn.io/fake"),
                )
            ],
        )
        utils.handle_user_message(message)


def test_handle_user_message_succeeds(mocker):
    # Mock external deps
    save_file_action = mocker.patch("api.datastore.insert_thread")
    mocked_resp = mocker.Mock(
        headers=__make_header(
            {
                "Date": "Thu, 04 Jan 2024 03:30:00 GMT",
                "Content-Type": "audio/x-wav",
                "Content-Disposition": "attachment; filename=oatmilk.wav",
            }
        ),
        status_code=200,
    )
    mocker.patch("requests.get", return_value=mocked_resp)
    message = facebook.Message(
        mid="kajhdisx",
        attachments=[
            facebook.Attachment(
                type="audio",
                payload=facebook.AttachmentPayload(url="tanwinn.io/fake"),
            )
        ],
    )
    utils.handle_user_message(message)

    save_file_action.assert_called_with(
        key="kajhdisx--0",
        audio_content=mocked_resp,
        dt=__from_ts("2024-01-03 19:30:00", "America/Los_Angeles"),
        title="oatmilk.wav",
        audio_type="wav",
    )
