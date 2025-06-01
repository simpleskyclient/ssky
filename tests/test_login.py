import os

from ssky.login import login
from ssky.profile_list import ProfileList
from ssky.ssky_session import SskySession
from tests.common import setup, teardown

def test_login_using_credentials():
    """Test login with handle:password credentials format"""
    SskySession.clear()
    setup(no_session_file=True)
    credentials = os.environ.get('SSKY_USER')
    result = login(credentials=credentials)
    with open(os.path.expanduser('~/.ssky'), 'r') as f:
        session_string = f.read()
    status = type(result) is ProfileList and session_string is not None
    teardown() 
    SskySession.clear()
    assert status

def test_login_using_environment_variable():
    """Test login using SSKY_USER environment variable"""
    SskySession.clear()
    setup(no_session_file=True)
    result = login()
    with open(os.path.expanduser('~/.ssky'), 'r') as f:
        session_string = f.read()
    status = type(result) is ProfileList and session_string is not None
    teardown()
    SskySession.clear()
    assert status

def test_login_using_session_file():
    """Test login using existing session file"""
    SskySession.clear()
    setup(envs_to_delete=['SSKY_USER'])
    result = login()
    with open(os.path.expanduser('~/.ssky'), 'r') as f:
        session_string = f.read()
    status = type(result) is ProfileList and session_string is not None
    teardown()
    SskySession.clear()
    assert status

def test_login_using_no_credentials():
    """Test login failure when no credentials available"""
    SskySession.clear()
    setup(envs_to_delete=['SSKY_USER'], no_session_file=True)
    result = login()
    status = result is None
    teardown()
    SskySession.clear()
    assert status