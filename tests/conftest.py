import pytest
import os
from tests.common import MasterSessionManager, setup, setup_with_session_copy
from ssky.ssky_session import SskySession

def pytest_sessionstart(session):
    """Called after the Session object has been created and configured.
    
    This is called before test collection starts.
    """
    # Clean up any existing master session backup before tests start
    MasterSessionManager.cleanup()
    
    # Create master session backup if existing session file is available
    # Do NOT perform login here to preserve test_00_login.py as the only API caller
    session_path = os.path.expanduser('~/.ssky')
    if os.path.exists(session_path):
        # Use existing session file to create backup
        backup_created = MasterSessionManager.create_from_current_session()
        if backup_created:
            print(f"\nCreated master session backup from existing session file")
    else:
        print(f"\nNo existing session file found at {session_path}")
        print("Non-login tests will be skipped until test_00_login.py creates a session")

def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished, right before returning the exit status to the system.
    
    This is the perfect place to clean up any test artifacts.
    """
    # Clean up master session backup file after all tests complete
    MasterSessionManager.cleanup()

@pytest.fixture(autouse=False)
def ssky_setup():
    """Basic setup fixture for tests that need environment setup"""
    setup()
    yield
    SskySession.clear()

@pytest.fixture(autouse=False)
def ssky_setup_no_session():
    """Setup fixture for tests that need clean environment without session file"""
    setup(no_session_file=True)
    yield
    SskySession.clear()

@pytest.fixture(autouse=False)
def ssky_setup_no_credentials():
    """Setup fixture for tests that need environment without credentials"""
    setup(envs_to_delete=['SSKY_USER'], no_session_file=True)
    yield
    SskySession.clear()

@pytest.fixture(autouse=False)
def ssky_setup_with_session_copy():
    """Setup fixture for tests that use copied session file"""
    def _setup_with_copy(envs_to_delete=[]):
        if not MasterSessionManager.exists():
            pytest.skip("Master session backup not available")
        
        SskySession.clear()
        setup_with_session_copy(
            master_session_path=MasterSessionManager.get_backup_path(),
            envs_to_delete=envs_to_delete
        )
        return True
    
    yield _setup_with_copy
    SskySession.clear()

@pytest.fixture(autouse=False)
def ssky_clean_environment():
    """Fixture for tests that need completely clean environment"""
    SskySession.clear()
    yield
    SskySession.clear()

# Login test specific fixtures
@pytest.fixture(autouse=False)
def ssky_login_fresh_environment():
    """Fixture for login tests that need fresh environment for session creation"""
    SskySession.clear()
    setup(no_session_file=True)
    yield
    SskySession.clear()

@pytest.fixture(autouse=False)
def ssky_login_session_only():
    """Fixture for login tests that use session file without credentials"""
    def _setup_session_only():
        if not MasterSessionManager.exists():
            pytest.skip("Master session backup not available")
        
        SskySession.clear()
        setup_with_session_copy(
            master_session_path=MasterSessionManager.get_backup_path(),
            envs_to_delete=[]  # Keep credentials for session file validation
        )
        return True
    
    yield _setup_session_only
    SskySession.clear() 