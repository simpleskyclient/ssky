import os
from ssky.profile import profile
from ssky.profile_list import ProfileList
from tests.common import setup, teardown

def test_profile_handle():
    setup()
    result = profile(os.environ.get('SSKY_TEST_HANDLE'))
    teardown()
    assert type(result) is ProfileList

def test_profile_did():
    setup()
    result = profile(os.environ.get('SSKY_TEST_DID'))
    teardown()
    assert type(result) is ProfileList

def test_profile_invalid_handle():
    setup()
    result = profile(os.environ.get('SSKY_TEST_INVALID_HANDLE'))
    teardown()
    assert result is None

def test_profile_invalid_did():
    setup()
    result = profile(os.environ.get('SSKY_TEST_INVALID_DID'))
    teardown()
    assert result is None