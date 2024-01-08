"""
unittests.test_models.py
~~~~~~~~~~~~~~~~~
Test ~/models
"""

from pprint import pformat as pf

import pytest
from pydantic import ValidationError

from models import facebook, weaver
import datetime

class TestFacebook:
    """Test Facebook models"""

    def test_valid_user(self):
        kwargs = {"id": "18722912"}
        assert kwargs == facebook.User(**kwargs).model_dump(exclude_unset=True)

    @pytest.mark.parametrize("id", ([], None))
    def test_invalid_user(self, id):
        with pytest.raises(ValidationError):
            facebook.User(id=id).model_dump(exclude_unset=True)

    def test_valid_messaging(self, test_fixture_valid_messaging):
        facebook.Messaging(**test_fixture_valid_messaging)

    def test_valid_message(self, test_fixture_valid_message):
        print(f"Test Data:\n{pf(test_fixture_valid_message)}")
        facebook.Message(**test_fixture_valid_message)

    def test_valid_event(self, test_fixture_valid_event):
        print(f"Test Data:\n{pf(test_fixture_valid_event)}")
        facebook.Event(**test_fixture_valid_event)

    def test_invalid_event(self, test_fixture_invalid_event):
        print(f"Test Data:\n{pf(test_fixture_invalid_event)}")
        with pytest.raises(ValidationError):
            facebook.Event(**test_fixture_invalid_event)
            
class TestWeaver:
    """Test weaver models"""
    
    def test_valid_sound_thread_metadata(self, test_fixture_valid_st_metadata):
        print(f"Test Data:\n{pf(test_fixture_valid_st_metadata)}")
        weaver.SoundThreadMetadata(**test_fixture_valid_st_metadata)
    
    def test_invalid_sound_thread_metadata(self, test_fixture_invalid_st_metadata):
        print(f"Test Data:\n{pf(test_fixture_invalid_st_metadata)}")
        with pytest.raises(ValidationError):    
            weaver.SoundThreadMetadata(**test_fixture_invalid_st_metadata)