import os
import tempfile
import pytest
from unittest.mock import patch, Mock

from ssky.login import login
from ssky.profile_list import ProfileList
from ssky.ssky_session import SskySession
from tests.common import (
    setup, teardown, create_master_session_backup, 
    setup_with_session_copy, cleanup_session_file, create_mock_atproto_client
)

class TestLoginSequential:
    """Sequential login tests to minimize Bluesky API calls
    
    Strategy: 1 real authentication + session file copying for other tests
    This reduces API calls from 4 to 1 per test run, avoiding rate limits.
    """
    
    master_session_backup = None
    
    @classmethod
    def setup_class(cls):
        """Class setup - prepare temporary file for session backup"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.master_session_backup = os.path.join(cls.temp_dir, 'master_session.json')
    
    @classmethod
    def teardown_class(cls):
        """Class teardown - cleanup temporary files"""
        if cls.master_session_backup and os.path.exists(cls.master_session_backup):
            os.remove(cls.master_session_backup)
        if hasattr(cls, 'temp_dir') and os.path.exists(cls.temp_dir):
            os.rmdir(cls.temp_dir)
    
    def test_01_create_master_session(self):
        """Master session creation - ONLY test that performs real Bluesky authentication
        
        This test makes the single API call to Bluesky and creates a session backup
        for other tests to use.
        """
        # Clear any existing session
        SskySession.clear()
        cleanup_session_file()
        
        # Setup with fresh credentials
        setup(no_session_file=True)
        
        # Get credentials from environment
        credentials = os.environ.get('SSKY_USER')
        if not credentials:
            pytest.skip("SSKY_USER environment variable not set")
        
        # Perform real authentication (the only API call in this test suite)
        result = login(credentials=credentials)
        
        # Verify successful login
        assert isinstance(result, ProfileList), "Login should return ProfileList"
        
        # Verify session file was created
        session_path = os.path.expanduser('~/.ssky')
        assert os.path.exists(session_path), "Session file should be created"
        
        # Read and verify session content
        with open(session_path, 'r') as f:
            session_content = f.read()
        assert session_content, "Session file should not be empty"
        
        # Create backup for other tests
        backup_created = create_master_session_backup(self.master_session_backup)
        assert backup_created, "Master session backup should be created"
        
        # Cleanup
        teardown()
        SskySession.clear()
    
    def test_02_login_using_session_file(self):
        """Test login using existing session file (no API calls)
        
        Uses the session file created by test_01, no network calls.
        """
        # Skip if master session not available
        if not os.path.exists(self.master_session_backup):
            pytest.skip("Master session backup not available")
        
        # Clear session and setup with copied session file
        SskySession.clear()
        setup_with_session_copy(
            master_session_path=self.master_session_backup,
            envs_to_delete=['SSKY_USER']  # Remove credentials to force session file usage
        )
        
        # Login using session file (no API call)
        result = login()
        
        # Verify successful login
        assert isinstance(result, ProfileList), "Login should return ProfileList"
        
        # Verify session file exists and has content
        session_path = os.path.expanduser('~/.ssky')
        assert os.path.exists(session_path), "Session file should exist"
        
        with open(session_path, 'r') as f:
            session_content = f.read()
        assert session_content, "Session file should not be empty"
        
        # Cleanup
        teardown()
        SskySession.clear()
    
    def test_03_login_credential_parsing(self):
        """Test credential parsing logic with mocked API calls
        
        Tests the credential parsing without making real API calls.
        """
        # Skip if master session not available (needed for environment setup)
        if not os.path.exists(self.master_session_backup):
            pytest.skip("Master session backup not available")
        
        SskySession.clear()
        cleanup_session_file()
        
        # Setup environment
        setup(no_session_file=True)
        
        # Create mock client
        mock_client, mock_profile = create_mock_atproto_client()
        
        # Test credential parsing with mock
        with patch('atproto.Client') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Test with explicit credentials
            credentials = "test.handle:testpassword"
            result = login(credentials=credentials)
            
            # Verify mock was called correctly
            mock_client.login.assert_called_once()
            call_args = mock_client.login.call_args
            
            # Verify credentials were parsed correctly
            assert 'login' in call_args.kwargs or len(call_args.args) >= 1
            assert 'password' in call_args.kwargs or len(call_args.args) >= 2
            
            # Verify result
            assert isinstance(result, ProfileList), "Should return ProfileList"
        
        # Cleanup
        teardown()
        SskySession.clear()
    
    def test_04_login_error_scenarios(self):
        """Test error handling without real API calls
        
        Tests various error conditions that the login function can handle.
        """
        SskySession.clear()
        cleanup_session_file()
        
        # Test 1: No credentials available
        setup(envs_to_delete=['SSKY_USER'], no_session_file=True)
        result = login()
        assert result is None, "Login should fail when no credentials available"
        
        # Test 2: Mock AtProtocolError during session creation
        setup(no_session_file=True)
        
        # Mock SskySession to raise AtProtocolError (which login() catches)
        import atproto_client
        
        with patch('ssky.login.SskySession') as mock_session_class:
            # Mock session that raises AtProtocolError
            mock_session_class.side_effect = atproto_client.exceptions.AtProtocolError("Mock authentication failed")
            
            # Set up environment variable for credentials
            os.environ['SSKY_USER'] = 'test.handle:testpassword'
            
            # This should handle the exception gracefully and return None
            result = login()
            assert result is None, "Login should return None on AtProtocolError"
        
        # Test 3: Test credential parsing with empty string
        result = login(credentials="")
        assert result is None, "Login should return None for empty credentials"
        
        # Test 4: Test credential parsing with invalid format (no colon)
        result = login(credentials="invalid_format")
        assert result is None, "Login should return None for invalid credential format"
        
        # Cleanup
        teardown()
        SskySession.clear()