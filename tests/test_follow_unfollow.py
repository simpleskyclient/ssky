import os
from ssky.profile_list import ProfileList
from ssky.follow import follow
from ssky.unfollow import unfollow
from tests.common import setup, teardown

def test_follow_by_handle():
    setup()
    result = follow(os.environ.get('SSKY_TEST_HANDLE'))
    teardown()
    assert type(result) is ProfileList

def test_unfollow_by_handle():
    setup(interval=5)
    result = unfollow(os.environ.get('SSKY_TEST_HANDLE'))
    teardown()
    assert type(result) is ProfileList

def test_unfollow_by_not_following_handle():
    setup(interval=5)
    result = unfollow(os.environ.get('SSKY_TEST_HANDLE'))
    teardown()
    assert result is None

def test_follow_by_did():
    setup()
    result = follow(os.environ.get('SSKY_TEST_DID'))
    teardown()
    assert type(result) is ProfileList

def test_unfollow_by_did():
    setup(interval=5)
    result = unfollow(os.environ.get('SSKY_TEST_DID'))
    teardown()
    assert type(result) is ProfileList

def test_unfollow_by_not_following_did():
    setup(interval=5)
    result = unfollow(os.environ.get('SSKY_TEST_DID'))
    teardown()
    assert result is None

def test_follow_by_invalid_did():
    setup()
    result = follow(os.environ.get('SSKY_TEST_INVALID_DID'))
    teardown()
    assert result is None

def test_unfollow_by_invalid_did():
    setup()
    result = unfollow(os.environ.get('SSKY_TEST_INVALID_DID'))
    teardown()
    assert result is None