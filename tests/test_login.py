import os

from ssky.login import login
from ssky.ssky_session import SskySession
from tests.common import setup, teardown

def test_login_with_handle_and_password():
    SskySession.clear()
    setup(no_session_file=True)
    handle, password = os.environ.get('SSKY_USER').split(':')
    result = login(handle=handle, password=password)
    with open(os.path.expanduser('~/.ssky'), 'r') as f:
        session_string = f.read()
    status = len(result) == 2 and type(result[0]) is str and type(result[1]) is str and session_string is not None
    teardown()
    SskySession.clear()
    assert status

def test_login_with_no_args_and_from_session_file():
    SskySession.clear()
    setup(envs_to_delete=['SSKY_USER'])
    result = login()
    status = result is not None and len(result) == 2 and type(result[0]) is str and type(result[1]) is str
    teardown()
    SskySession.clear()
    assert status

def test_login_with_no_args_and_from_env():
    SskySession.clear()
    setup(no_session_file=True)
    result = login()
    status = result is not None and len(result) == 2 and type(result[0]) is str and type(result[1]) is str
    teardown()
    SskySession.clear()
    assert status

def test_login_with_no_args_and_no_env():
    SskySession.clear()
    setup(envs_to_delete=['SSKY_USER'], no_session_file=True)
    result = login()
    status = result is None
    teardown()
    SskySession.clear()
    assert status

def test_login_with_handle_and_no_password():
    SskySession.clear()
    setup(envs_to_delete=['SSKY_USER'], no_session_file=True)
    result = login(handle=os.environ.get('SSKY_HANDLE'), password=None)
    status = result is None
    teardown()
    SskySession.clear()
    assert status

def test_login_with_no_handle_and_password():
    SskySession.clear()
    setup(envs_to_delete=['SSKY_USER'], no_session_file=True)
    result = login(handle=None, password=os.environ.get('SSKY_PASSWORD'))
    status = result is None
    teardown()
    SskySession.clear()
    assert status