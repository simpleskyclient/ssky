import os
from ssky.post_data_list import PostDataList
from ssky.search import search
from tests.common import setup, teardown

def test_search_q():
    setup()
    result = search(os.environ.get('SSKY_TEST_Q'))
    teardown()
    assert type(result) is PostDataList

def test_search_q_with_limit():
    setup()
    result = search(os.environ.get('SSKY_TEST_Q'), limit=int(os.environ.get('SSKY_TEST_LIMIT')))
    teardown()
    assert type(result) is PostDataList and len(result) == int(os.environ.get('SSKY_TEST_LIMIT'))

def test_search_q_with_no_results():
    setup()
    result = search(os.environ.get('SSKY_TEST_Q_WITH_NO_RESULTS'))
    teardown()
    assert type(result) is PostDataList

def test_search_with_actor_handle():
    setup()
    result = search(os.environ.get('SSKY_TEST_Q'), actor=os.environ.get('SSKY_TEST_USER_HANDLE'))
    teardown()
    assert type(result) is PostDataList

def test_search_with_actor_did():
    setup()
    result = search(os.environ.get('SSKY_TEST_Q'), actor=os.environ.get('SSKY_TEST_USER_DID'))
    teardown()
    assert type(result) is PostDataList

def test_search_with_period():
    setup()
    result = search(os.environ.get('SSKY_TEST_Q'), since=os.environ.get('SSKY_TEST_SINCE'), until=os.environ.get('SSKY_TEST_UNTIL'))
    teardown()
    assert type(result) is PostDataList

def test_search_with_period_only_beginning():
    setup()
    result = search(os.environ.get('SSKY_TEST_Q'), since=os.environ.get('SSKY_TEST_SINCE'))
    teardown()
    assert type(result) is PostDataList

def test_search_with_period_only_end():
    setup()
    result = search(os.environ.get('SSKY_TEST_Q'), until=os.environ.get('SSKY_TEST_SINCE'))
    teardown()
    assert type(result) is PostDataList

def test_search_with_invalid_period():
    setup()
    result = search(os.environ.get('SSKY_TEST_Q'), since=os.environ.get('SSKY_TEST_INVALID_SINCE'), until=os.environ.get('SSKY_TEST_INVALID_UNTIL'))
    teardown()
    assert result is None