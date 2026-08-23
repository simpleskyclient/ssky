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

def pytest_collection_modifyitems(config, items):
    """Honor SSKY_SKIP_REAL_API_TESTS for the whole real_api tier.

    Kept for one release so existing invocations keep working. The markers are the
    real mechanism: a default run already excludes real_api via addopts, so this
    only matters when someone selects the tier explicitly and still sets the flag.
    """
    if not os.environ.get('SSKY_SKIP_REAL_API_TESTS'):
        return
    skip_real = pytest.mark.skip(reason="Real API tests disabled by SSKY_SKIP_REAL_API_TESTS")
    for item in items:
        if item.get_closest_marker('real_api') or item.get_closest_marker('write_api'):
            item.add_marker(skip_real)


@pytest.fixture
def require_test_account():
    """Refuse to mutate any account other than the declared test account.

    Marker selection decides whether a write test is *collected*; this decides
    whether it may actually run. SSKY_TEST_ACCOUNT_DID is compared against the DID
    the session is logged in as, because a handle can be reassigned and a DID
    cannot. Without the variable, write tests never run.
    """
    from tests.common import has_credentials, read_test_config

    # Read this one value out of tests/.env directly instead of loading the file over
    # the environment. Making tests/.env win over the ambient SSKY_USER looks tidier,
    # but combined with setup(no_session_file=True) deleting ~/.ssky it ends up
    # persisting the test account's session into the developer's session file, which
    # silently switches which account their CLI is logged in as (#108).
    expected_did = read_test_config('SSKY_TEST_ACCOUNT_DID')
    if not expected_did:
        pytest.skip(
            "SSKY_TEST_ACCOUNT_DID is not set. Write tests mutate a live account, "
            "so they only run against the account declared there."
        )
    if not has_credentials():
        pytest.skip("SSKY_USER environment variable not set")

    SskySession.clear()
    profile = SskySession().profile()
    actual_did = getattr(profile, 'did', None) if profile is not None else None
    if actual_did != expected_did:
        SskySession.clear()
        pytest.skip(
            f"Logged in as {actual_did or 'an unauthenticated session'}, but write tests "
            f"are restricted to {expected_did}. Refusing to mutate this account."
        )
    yield actual_did
    SskySession.clear()


@pytest.fixture(autouse=True)
def block_real_login(request, monkeypatch):
    """Fail loudly instead of authenticating, for everything outside the real_api tier.

    The default tier promises no network access, and asserting that once is not enough
    to keep it true. Commands reach the session through several doors — ssky_client(),
    expand_actor(), and SskySession() constructed directly — so a test that patches only
    the door it knows about still authenticates for real. Blocking the one function that
    actually talks to the API turns that into a visible failure instead of a silent
    network call, which is how five such tests went unnoticed.
    """
    if request.node.get_closest_marker('real_api') or \
            request.node.get_closest_marker('needs_session'):
        return

    def _blocked(cls, handle=None, password=None, session_string=None):
        raise AssertionError(
            "This test authenticated against the live Bluesky API. Complete its mocks "
            "(ssky_client alone is often not enough - see expand_actor and "
            "profile_list.SskySession) or mark it @pytest.mark.real_api."
        )

    monkeypatch.setattr(SskySession, 'at_login_internal', classmethod(_blocked))
