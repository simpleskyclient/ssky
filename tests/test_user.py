import os
from ssky.profile_list import ProfileList
from ssky.user import user
from tests.common import setup, teardown

def test_user_q():
    setup()
    result = user(os.environ.get('SSKY_TEST_Q'))
    teardown()
    assert type(result) is ProfileList

def test_user_q_with_limit():
    setup()
    result = user(os.environ.get('SSKY_TEST_Q'), limit=int(os.environ.get('SSKY_TEST_LIMIT')))
    teardown()
    assert type(result) is ProfileList and len(result) == int(os.environ.get('SSKY_TEST_LIMIT'))

def test_user_q_with_no_results():
    setup()
    result = user(os.environ.get('SSKY_TEST_Q_WITH_NO_RESULTS'))
    teardown()
    assert type(result) is ProfileList