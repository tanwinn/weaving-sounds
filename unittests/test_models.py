"""
unittests.test_models.py
~~~~~~~~~~~~~~~~~
Test ~/models
todo: Use examples here for testing instead
https://developers.facebook.com/docs/messenger-platform/reference/webhook-events/messages
"""

from pprint import pformat as pf

import pytest
from pydantic import ValidationError

from models import facebook, weaver


class TestFacebook:
    """Test Facebook models"""

    def test_valid_user(self):
        kwargs = {"id": "18722912"}
        assert kwargs == facebook.User.model_validate(kwargs).model_dump(
            exclude_unset=True
        )

    @pytest.mark.parametrize("id", ([], None))
    def test_invalid_user(self, id):
        with pytest.raises(ValidationError):
            facebook.User(id=id).model_dump(exclude_unset=True)

    def test_valid_messaging(self, test_fixture_valid_messaging):
        facebook.Messaging.model_validate(test_fixture_valid_messaging)

    def test_valid_message(self, test_fixture_valid_message):
        print(f"Test Data:\n{pf(test_fixture_valid_message)}")
        facebook.Message.model_validate(test_fixture_valid_message)

    def test_invalid_message(self, test_fixture_invalid_message):
        print(f"Test Data:\n{pf(test_fixture_invalid_message)}")
        with pytest.raises(ValidationError):
            facebook.Message.model_validate(test_fixture_invalid_message)

    def test_valid_event(self, test_fixture_valid_event):
        print(f"Test Data:\n{pf(test_fixture_valid_event)}")
        facebook.Event.model_validate(test_fixture_valid_event)

    def test_invalid_event(self, test_fixture_invalid_event):
        print(f"Test Data:\n{pf(test_fixture_invalid_event)}")
        with pytest.raises(ValidationError):
            facebook.Event.model_validate(test_fixture_invalid_event)


class TestWeaver:
    """Test weaver models"""

    def test_valid_voice_metadata(self, test_fixture_valid_voice_metadata):
        print(f"Test Data:\n{pf(test_fixture_valid_voice_metadata)}")
        weaver.VoiceMetadata.model_validate(test_fixture_valid_voice_metadata)

    def test_invalid_voice_metadata(self, test_fixture_invalid_voice_metadata):
        print(f"Test Data:\n{pf(test_fixture_invalid_voice_metadata)}")
        with pytest.raises(ValidationError):
            weaver.VoiceMetadata.model_validate(test_fixture_invalid_voice_metadata)

    def test_valid_user(self, test_fixture_valid_user):
        print(f"Test Data:\n{pf(test_fixture_valid_user)}")
        weaver.User.model_validate(test_fixture_valid_user)

    def test_invalid_user(self, test_fixture_invalid_user):
        print(f"Test Data:\n{pf(test_fixture_invalid_user)}")
        with pytest.raises(ValidationError):
            weaver.User.model_validate(test_fixture_invalid_user)

    def test_valid_prompt(self, test_fixture_valid_prompt):
        print(f"Test Data:\n{pf(test_fixture_valid_prompt)}")
        weaver.Prompt.model_validate(test_fixture_valid_prompt)

    def test_invalid_prompt(self, test_fixture_invalid_prompt):
        print(f"Test Data:\n{pf(test_fixture_invalid_prompt)}")
        with pytest.raises(ValidationError):
            weaver.Prompt.model_validate(test_fixture_invalid_prompt)
