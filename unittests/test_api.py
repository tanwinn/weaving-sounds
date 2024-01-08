"""
tests.test_api.py
~~~~~~~~~~~~~~~~~
Test api calls
"""

import pytest

import api

def test_client(api_client_fixture):
    assert api_client_fixture


def test_lifespan(api_client_fixture, mocker):
    """Test app's startup and shutdown lifespan events."""
    on_startup = mocker.patch("api.datastore.load_memory_from_storage")
    on_shutdown = mocker.patch("api.datastore.load_storage_from_memory")
    
    with api_client_fixture:
        # After startup
        on_startup.assert_called_once()

    # After shutdown
    on_shutdown.assert_called_once()


@pytest.mark.parametrize(
    "params", ["hub.verify_token=invalid", "hub.verify_token=foo&hub.challenge=bar"]
)
def test_webhook_always_return_200(api_client_fixture, params):
    assert api_client_fixture.get(f"/webhook?{params}").status_code == 200


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
    assert response.json() == "Invalid Request or Verification Token"
    monkeypatch.undo()


@pytest.mark.parametrize("token,challenge", [("foo", 123), ("flamingo", "ant")])
def test_get_webhook_succeeded(api_client_fixture, token, challenge, monkeypatch):
    monkeypatch.setattr(api.main, "FB_VERIFY_TOKEN", value=token)
    response = api_client_fixture.get(
        f"/webhook?hub.verify_token={token}&hub.challenge={challenge}&hub.mode=subscribe"
    )
    assert response.json() == challenge
    monkeypatch.undo()


def test_get_privacy_policy(api_client_fixture):
    assert api_client_fixture.get("/privacy-policy").status_code == 200


def test_post_message_200_resp_valid_data(
    api_client_fixture, test_fixture_valid_event, mocker
):
    mocker.patch("api.utils.handle_user_message", return_value="mocked response")
    resp = api_client_fixture.post(f"/webhook", json=test_fixture_valid_event)
    assert resp.status_code == 200

