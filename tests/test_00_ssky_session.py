import os
import json
import pytest
from unittest.mock import patch, Mock

from ssky.ssky_session import SskySession
from tests.common import (
    setup, BaseSequentialTest,
    MasterSessionManager, has_credentials
)

class TestSskySessionSequential(BaseSequentialTest):
    """Sequential SskySession tests - the ONLY tests that use real atproto
    
    Strategy: Test SskySession functionality with real Bluesky API calls
    and create session backup for other tests to use.
    """
    
    def test_01_session_login_and_persistence(self):
        """Test SskySession login with real credentials and session persistence
        
        This is the ONLY test that makes real API calls to Bluesky.
        """
        session_path = os.path.expanduser('~/.ssky')
        
        # Check if session file already exists
        if os.path.exists(session_path):
            # Issue warning and skip actual login
            import warnings
            warnings.warn(
                f"Session file {session_path} already exists. "
                "Skipping real Bluesky authentication and using existing session file. "
                "Delete the file if you want to perform fresh authentication.",
                UserWarning
            )
            
            # Verify existing session file has content
            with open(session_path, 'r') as f:
                session_content = f.read()
            assert session_content, "Existing session file should not be empty"
            
            # Test session loading from existing file
            SskySession.clear()
            session = SskySession()
            assert SskySession.status() == SskySession.Status.LOGGED_IN, "Should be logged in from existing session"
            
            # Create backup for other tests using existing session
            backup_created = MasterSessionManager.create_from_current_session()
            assert backup_created, "Master session backup should be created from existing session"
            
            SskySession.clear()
            return  # Skip the actual login process
        
        # Clear any existing session
        SskySession.clear()
        
        # Setup with fresh credentials
        setup(no_session_file=True)
        
        # Check for credentials
        if not has_credentials():
            pytest.skip("SSKY_USER environment variable not set")
        
        # Get credentials from environment
        credentials = os.environ.get('SSKY_USER')
        handle, password = credentials.split(':', 1)
        
        # Test 1: Create session with credentials
        session = SskySession(handle=handle, password=password)
        assert SskySession.status() == SskySession.Status.LOGGED_IN, "Should be logged in"
        
        # Test 2: Verify client and profile are available
        client = session.client()
        assert client is not None, "Client should be available"
        
        profile = session.profile()
        assert profile is not None, "Profile should be available"
        assert hasattr(profile, 'did'), "Profile should have DID"
        assert profile.did is not None, "Profile DID should not be None"
        
        # Test 3: Session persistence
        session.persist()
        assert os.path.exists(session_path), "Session file should be created"
        
        # Test 4: Verify session file content
        with open(session_path, 'r') as f:
            session_data = json.load(f)
        assert 'session_string' in session_data, "Session file should contain session_string"
        assert session_data['session_string'], "Session string should not be empty"
        
        # Test 5: Clear and reload session from file
        SskySession.clear()
        assert SskySession.status() == SskySession.Status.NOT_LOGGED_IN, "Should be logged out after clear"
        
        # Create new session (should load from file)
        session2 = SskySession()
        assert SskySession.status() == SskySession.Status.LOGGED_IN, "Should be logged in from file"
        
        # Verify client and profile are still available
        client2 = session2.client()
        assert client2 is not None, "Client should be available from persisted session"
        
        profile2 = session2.profile()
        assert profile2 is not None, "Profile should be available from persisted session"
        assert profile2.did == profile.did, "Profile DID should match original"
        
        # Create backup for other tests
        backup_created = MasterSessionManager.create_from_current_session()
        assert backup_created, "Master session backup should be created"
        
        # Cleanup
        SskySession.clear()
    
    def test_02_session_status_management(self):
        """Test SskySession status management without API calls"""
        
        # Test 1: Initial state
        SskySession.clear()
        assert SskySession.status() == SskySession.Status.NOT_LOGGED_IN, "Initial status should be NOT_LOGGED_IN"
        
        # Test 2: Login failed state
        SskySession.session = SskySession.login_failed
        assert SskySession.status() == SskySession.Status.LOGIN_FAILED, "Status should be LOGIN_FAILED"
        
        # Test 3: Clear function
        SskySession.clear()
        assert SskySession.status() == SskySession.Status.NOT_LOGGED_IN, "Status should be NOT_LOGGED_IN after clear"
        assert SskySession.session is None, "Session should be None after clear"
        
        # Cleanup
        SskySession.clear()
    
    def test_03_session_error_handling(self):
        """Test SskySession error handling with invalid credentials"""
        
        SskySession.clear()
        setup(no_session_file=True)
        
        # Test with invalid credentials (should cause login failure)
        with patch('ssky.ssky_session.atproto.Client') as mock_client_class:
            import atproto_client
            mock_client = Mock()
            mock_client.login.side_effect = atproto_client.exceptions.AtProtocolError("Invalid credentials")
            mock_client_class.return_value = mock_client
            
            # This should set session to login_failed (not raise exception)
            session = SskySession(handle="invalid", password="invalid")
            assert SskySession.status() == SskySession.Status.LOGIN_FAILED, "Status should be LOGIN_FAILED for invalid credentials"
            
            # Test client() method with failed session
            client = session.client()
            assert client is None, "Client should be None for failed session"
            
            # Test profile() method with failed session
            profile = session.profile()
            assert profile is None, "Profile should be None for failed session"
        
        # Cleanup
        SskySession.clear()
    
    def test_04_session_without_credentials(self):
        """Test SskySession behavior when no credentials are available"""
        
        SskySession.clear()
        
        # Manually clean environment - don't use setup() which loads .env
        import os
        if 'SSKY_USER' in os.environ:
            del os.environ['SSKY_USER']
        
        # Test session creation without credentials and without session file
        # With current implementation, this raises LoginRequiredError
        import atproto_client
        
        with pytest.raises(atproto_client.exceptions.LoginRequiredError):
            session = SskySession()
        
        # After the failed initialization, session should be in login_failed state
        assert SskySession.status() == SskySession.Status.LOGIN_FAILED, "Status should be LOGIN_FAILED without credentials"
        
        # Create a session object to test the methods (even though init failed)
        # The session object itself can be created, but the class state is login_failed
        session = SskySession.__new__(SskySession)  # Create without calling __init__
        
        # Test that client and profile return None for failed session
        client = session.client()
        assert client is None, "Client should be None for failed session"
        
        profile = session.profile()
        assert profile is None, "Profile should be None for failed session"
        
        # persist() should do nothing for failed session
        session.persist()  # Should not raise
        
        # Cleanup
        SskySession.clear() 