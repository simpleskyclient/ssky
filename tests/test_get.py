import os
from ssky.get import get
from ssky.post_data_list import PostDataList
from tests.common import setup, teardown

def test_get_timeline():
    setup()
    result = get(target=None)
    teardown()
    assert type(result) is PostDataList

def test_get_myself():
    setup()
    result = get(target='myself')
    teardown()
    assert type(result) is PostDataList

def test_get_with_actor_handle():
    setup()
    result = get(target=os.environ.get('SSKY_TEST_HANDLE'))
    teardown()
    assert type(result) is PostDataList

def test_get_with_actor_did():
    setup()
    result = get(target=os.environ.get('SSKY_TEST_DID'))
    teardown()
    assert type(result) is PostDataList

def test_get_with_at_uri():
    setup()
    result = get(target=os.environ.get('SSKY_TEST_URI'))
    teardown()
    assert type(result) is PostDataList

def test_get_with_at_uri_cid():
    setup()
    result = get(target=os.environ.get('SSKY_TEST_URI_CID'))
    teardown()
    assert type(result) is PostDataList

def test_get_with_invalid_actor_handle():
    setup()
    result = get(target=os.environ.get('SSKY_TEST_INVALID_HANDLE'))
    teardown()
    assert result is None

def test_get_with_invalid_actor_did():
    setup()
    result = get(target=os.environ.get('SSKY_TEST_INVALID_DID'))
    teardown()
    assert result is None

def test_get_with_invalid_uri():
    setup()
    result = get(target=os.environ.get('SSKY_TEST_INVALID_URI'))
    teardown()
    assert result is None

def test_get_with_invalid_uri_cid():
    setup()
    result = get(target=os.environ.get('SSKY_TEST_INVALID_URI_CID'))
    teardown()
    assert result is None