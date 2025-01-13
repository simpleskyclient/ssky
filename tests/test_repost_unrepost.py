import os
from ssky.post_data_list import PostDataList
from ssky.repost import repost
from ssky.unrepost import unrepost
from tests.common import setup, teardown

def test_repost_by_uri():
    setup()
    result = repost(os.environ.get('SSKY_TEST_URI'))
    teardown()
    assert type(result) is PostDataList

def test_unrepost_by_uri():
    setup(interval=5)
    result = unrepost(os.environ.get('SSKY_TEST_URI'))
    teardown()
    assert type(result) is PostDataList

def test_unrepost_by_not_reposted_uri():
    setup(interval=5)
    result = unrepost(os.environ.get('SSKY_TEST_URI'))
    teardown()
    assert result is None

def test_repost_by_uri_cid():
    setup()
    result = repost(os.environ.get('SSKY_TEST_URI_CID'))
    teardown()
    assert type(result) is PostDataList

def test_unrepost_by_uri_cid():
    setup(interval=5)
    result = unrepost(os.environ.get('SSKY_TEST_URI_CID'))
    teardown()
    assert type(result) is PostDataList

def test_unrepost_by_not_reposted_uri_cid():
    setup(interval=5)
    result = unrepost(os.environ.get('SSKY_TEST_URI_CID'))
    teardown()
    assert result is None

def test_repost_by_invalid_uri():
    setup()
    result = repost(os.environ.get('SSKY_TEST_INVALID_URI'))
    teardown()
    assert result is None

def test_unrepost_by_invalid_uri():
    setup()
    result = unrepost(os.environ.get('SSKY_TEST_INVALID_URI'))
    teardown()
    assert result is None