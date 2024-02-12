"""
unittests.test_utils.py
~~~~~~~~~~~~~~~~~~~~~~~
Unittest for api.utils models
"""
import re
from collections.abc import Mapping
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import pytest
import requests
import responses

from api import datastore, utils
from models import facebook


def __from_ts(ts: str, tz: Optional[str] = "UTC") -> datetime:
    """Convert timestamp with the format `2024-01-03 19:30:00` to datetime object with UTC timezone."""
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo(tz))


def __make_header(header_data: Mapping) -> requests.structures.CaseInsensitiveDict:
    """Convert a normal dictionary to case-insenstive http header similar to real object passed."""
    return requests.structures.CaseInsensitiveDict(header_data)


@pytest.mark.parametrize(
    "header_data,expected_ts",
    [
        ({"Date": "Thu, 04 Jan 2024 03:30:00 GMT"}, "2024-01-04 03:30:00"),
        ({"last-modified": "Thu, 04 Jan 2024 16:00:00 GMT"}, "2024-01-04 16:00:00"),
    ],
)
def test_extract_header_datetime_default_tz(header_data: Mapping, expected_ts: str):
    header = __make_header(header_data)
    expected = __from_ts(expected_ts)
    assert utils.extract_header_datetime(header) == expected


def test_extract_header_datetime_invalid_header():
    header = __make_header({"header_no_date": "delilmama"})
    # Expecting now time, return without problem and with a timezone
    now = utils.extract_header_datetime(header)
    assert now.tzinfo.key == "UTC"


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
    mocker.patch("api.datastore.insert_voice")
    invalid_msg = facebook.Message.model_validate(msg_data)
    with pytest.raises(AttributeError):
        utils.handle_user_message("undefined_user", invalid_msg)


def test_handle_user_message_http_error(mocker):
    mocker.patch("api.datastore.insert_voice")
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
        utils.handle_user_message("undefined_user", message)


def test_handle_user_message_filetype_unknown(mocker):
    # Mock external deps
    mocker.patch("api.datastore.insert_voice")
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
        utils.handle_user_message("undefined_user", message)


def test_handle_user_message_succeeds(mocker):
    # Mock external deps
    save_file_action = mocker.patch("api.datastore.insert_voice")
    mocked_resp = mocker.Mock(
        headers=__make_header(
            {
                "Date": "Thu, 04 Jan 2024 03:30:00 GMT",
                "Content-Type": "audio/x-wav",
                "Content-Disposition": "attachment; filename=oatmilk.wav",
            }
        ),
        status_code=200,
        content=b"blub bluuub blub",
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
    utils.handle_user_message("fb/tanwinn", message)

    save_file_action.assert_called_with(
        id="kajhdisx-0",
        audio_content=b"blub bluuub blub",
        datetime=__from_ts("2024-01-04 03:30:00"),
        username="fb/tanwinn",
        audio_extension="wav",
        prompt_id=1,
    )


def test_handle_fb_user_already_registered(mocker):
    # Mock external deps to mimick that the user is already registered
    mocker.patch("api.datastore.get_user_by_id", return_value="user_found")
    register_new_user_action = mocker.patch("api.datastore.insert_user")
    assert utils.handle_fb_user("tanwinn") == "fb/tanwinn"
    register_new_user_action.assert_not_called()  # since user is already in the system, we didn't register new one


def test_handle_fb_user_new_http_error(mocker):
    # Mock external deps to mimick that the user is new
    mocker.patch("api.datastore.get_user_by_id", return_value=None)
    # http gets connection error
    mocker.patch("requests.get", side_effect=requests.exceptions.ConnectionError())
    with pytest.raises(requests.exceptions.HTTPError):
        utils.handle_fb_user("tanwinn")


@responses.activate
def test_handle_fb_user_new_registered_successfully(mocker):
    # Mock external deps
    # mimick that the user is new
    mocker.patch("api.datastore.get_user_by_id", return_value=None)

    # mock http gets
    # todo: config important env var using test env vars instead of mocking the os.environ
    access_token = "access+token+test"
    mocker.patch("os.environ.get", return_value=access_token)

    id = 123456789
    responses.add(
        responses.GET,
        re.compile("https://graph.facebook.com/v19.0/*"),
        json={"first_name": "Takenobu", "last_name": "Igarashi", "id": id},
        status=200,
    )

    register_new_user_action = mocker.patch("api.datastore.insert_user")

    assert utils.handle_fb_user(id) == f"fb/{id}"

    register_new_user_action.assert_called_once_with(
        f"fb/{id}", first_name="Takenobu", last_name="Igarashi"
    )


@responses.activate
def test_handle_fb_user_new_registered_no_name_successfully(mocker):
    # Mock external deps
    # mimick that the user is new
    mocker.patch("api.datastore.get_user_by_id", return_value=None)

    # mock http gets
    # todo: config important env var using test env vars instead of mocking the os.environ
    access_token = "access+token+test"
    mocker.patch("os.environ.get", return_value=access_token)

    id = 123456789
    responses.add(
        responses.GET,
        re.compile("https://graph.facebook.com/v19.0/*"),
        json={"id": id},
        status=200,
    )

    register_new_user_action = mocker.patch("api.datastore.insert_user")

    assert utils.handle_fb_user(id) == f"fb/{id}"

    register_new_user_action.assert_called_once_with(
        f"fb/{id}", first_name="undefined", last_name=None
    )


def test_datetime_from_timestamp():
    assert utils.datetime_from_ts("2024-01-04 03:30:00") == __from_ts(
        "2024-01-04 03:30:00"
    )
    assert utils.datetime_from_ts(
        "2024-01-04 03:30:00", "America/Los_Angeles"
    ) == __from_ts("2024-01-04 03:30:00", "America/Los_Angeles")
