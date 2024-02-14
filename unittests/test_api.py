"""
tests.test_api.py
~~~~~~~~~~~~~~~~~
Test api calls
"""

import pytest

import api
from models import weaver


def test_client(api_client_fixture):
    assert api_client_fixture


@pytest.fixture(autouse=True)
def _auto_mock_datastore(mocker):
    mocker.patch("api.datastore.startup")
    mocker.patch("api.datastore.clearall")
    mocker.patch("api.datastore.clearvoices")
    mocker.patch("api.datastore.shutdown")


def test_lifespan(api_client_fixture, mocker):
    """Test app's startup and shutdown lifespan events."""
    on_startup = mocker.patch("api.datastore.startup")
    on_shutdown = mocker.patch("api.datastore.shutdown")

    with api_client_fixture:
        # After startup
        on_startup.assert_called_once()

    # After shutdown
    on_shutdown.assert_called_once()


@pytest.mark.parametrize(
    "params",
    [
        "hub.verify_token=invalid&hub.mode=subscribe",
        "hub.verify_token=foo",
        "hub.verify_token=foobar&hub.mode=unsubscribe",
    ],
)
def test_get_webhook_failed(api_client_fixture, params, monkeypatch):
    monkeypatch.setattr(api.main, "FB_VERIFY_TOKEN", value="foobar")
    response = api_client_fixture.get(f"/webhook?{params}")
    assert response.status_code == 401
    assert response.content == b"Invalid Request or Verification Token"
    monkeypatch.undo()


@pytest.mark.parametrize("token,challenge", [("foo", 123), ("flamingo", "ant")])
def test_get_webhook_succeeded(api_client_fixture, token, challenge, monkeypatch):
    monkeypatch.setattr(api.main, "FB_VERIFY_TOKEN", value=token)
    response = api_client_fixture.get(
        f"/webhook?hub.verify_token={token}&hub.challenge={challenge}&hub.mode=subscribe"
    )
    assert response.status_code == 200
    assert response.json() == challenge
    monkeypatch.undo()


def test_get_privacy_policy(api_client_fixture):
    assert api_client_fixture.get("/privacy-policy").status_code == 200


def test_post_message_200_resp_valid_data(
    api_client_fixture, test_fixture_valid_event, mocker
):
    mocker.patch("api.utils.handle_fb_user", return_value="fb/12345")
    mocker.patch("api.utils.handle_user_message", return_value="mocked response")
    mocker.patch("api.utils.reply_to")
    resp = api_client_fixture.post("/webhook", json=test_fixture_valid_event)
    assert resp.status_code == 200


def test_post_message_422(api_client_fixture, test_fixture_invalid_event, mocker):
    mocker.patch("api.utils.handle_fb_user", return_value="fb/12345")
    mocker.patch("api.utils.handle_user_message", return_value="mocked response")
    mocker.patch("api.utils.reply_to")
    resp = api_client_fixture.post("/webhook", json=test_fixture_invalid_event)
    assert resp.status_code == 422


def test_get_users_unauthorized(api_client_fixture, monkeypatch):
    monkeypatch.setattr(api.main, "SECRET", value="right-secret")
    resp = api_client_fixture.get("/users", params={"secret": "wrong-secret"})
    assert resp.status_code == 401
    monkeypatch.undo()


def test_get_users_successfully(api_client_fixture, monkeypatch, mocker):
    user = weaver.User(
        _id="fb/123456",
        username="wasp",
        first_name="Bee",
        last_name="Fake",
    )
    mocker.patch("api.datastore.get_users", return_value=[user])
    monkeypatch.setattr(api.main, "SECRET", value="momofuku")
    resp = api_client_fixture.get("/users", params={"secret": "momofuku"})
    assert resp.status_code == 200
    assert resp.json()[0] == user.model_dump(exclude_unset=True)
    monkeypatch.undo()


def test_get_users_none_successfully(api_client_fixture, monkeypatch, mocker):
    mocker.patch("api.datastore.get_users", return_value=[])
    monkeypatch.setattr(api.main, "SECRET", value="momofuku")
    resp = api_client_fixture.get("/users", params={"secret": "momofuku"})
    assert resp.status_code == 200
    assert resp.json() == []
    monkeypatch.undo()
