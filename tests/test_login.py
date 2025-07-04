import os
import pytest
from unittest.mock import patch, Mock

from ssky.login import login
from ssky.profile_list import ProfileList
from ssky.result import (
    EmptyCredentialsError,
    InvalidCredentialFormatError,
    ProfileUnavailableAfterLoginError,
    AtProtocolSskyError
)
from tests.common import (
    create_mock_ssky_session, BaseSequentialTest,
    MasterSessionManager, has_credentials
)

@pytest.fixture
def mock_ssky_session():
    """Fixture that provides a mock SskySession for testing"""
    return create_mock_ssky_session()

@pytest.fixture
def login_environment():
    """Fixture that sets up login test environment"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('tests/.env')
    
    # Clear any existing session state
    from ssky.ssky_session import SskySession
    SskySession.clear()
    
    yield
    
    # Cleanup
    SskySession.clear()

@pytest.fixture
def credentials_available():
    """Fixture that checks if credentials are available"""
    if not has_credentials():
        pytest.skip("SSKY_USER environment variable not set")
    return True

class TestLoginSequential(BaseSequentialTest):
    """Login function tests using mocked SskySession
    
    These tests focus on the login() function logic without making real API calls.
    SskySession is mocked to avoid actual authentication.
    """
    
    def test_01_login_with_credentials_parameter(self, login_environment, mock_ssky_session):
        """Test login with explicit credentials parameter"""
        
        # Skip if master session not available for environment setup
        if not MasterSessionManager.exists():
            pytest.skip("Master session backup not available")
        
        # Unpack mock objects
        mock_session, mock_client, mock_profile = mock_ssky_session
        
        # Test credential parsing with mock
        with patch('ssky.login.SskySession') as mock_session_class:
            mock_session_class.return_value = mock_session
            
            # Test with explicit credentials
            credentials = "test.handle:testpassword"
            result = login(credentials=credentials)
            
            # Verify session was created with parsed credentials
            mock_session_class.assert_called_once()
            call_args = mock_session_class.call_args
            
            # Check if credentials were parsed correctly
            assert 'handle' in call_args.kwargs, "Should pass handle parameter"
            assert 'password' in call_args.kwargs, "Should pass password parameter"
            assert call_args.kwargs['handle'] == "test.handle", "Handle should be parsed correctly"
            assert call_args.kwargs['password'] == "testpassword", "Password should be parsed correctly"
            
            # Verify session methods were called
            mock_session.profile.assert_called_once()
            
            # Verify result
            assert isinstance(result, ProfileList), "Should return ProfileList"
    
    def test_02_login_with_environment_credentials(self, login_environment, credentials_available, mock_ssky_session):
        """Test login using SSKY_USER environment variable"""
        
        # Skip if master session not available for environment setup
        if not MasterSessionManager.exists():
            pytest.skip("Master session backup not available")
        
        # Unpack mock objects
        mock_session, mock_client, mock_profile = mock_ssky_session
        
        with patch('ssky.login.SskySession') as mock_session_class:
            mock_session_class.return_value = mock_session
            
            # Test login without explicit credentials (should use environment)
            result = login()
            
            # Verify session was created
            mock_session_class.assert_called_once()
            
            # Verify session methods were called
            mock_session.profile.assert_called_once()
            
            # Verify result
            assert isinstance(result, ProfileList), "Should return ProfileList"
    
    def test_03_login_credential_parsing_edge_cases(self, login_environment, mock_ssky_session):
        """Test credential parsing with various edge cases"""
        
        # Unpack mock objects
        mock_session, mock_client, mock_profile = mock_ssky_session
        
        # Test 1: Empty credentials
        with pytest.raises(EmptyCredentialsError):
            login(credentials="")
        
        # Test 2: Invalid format (no colon)
        with pytest.raises(InvalidCredentialFormatError):
            login(credentials="invalid_format")
        
        # Test 3: Only whitespace
        with pytest.raises(EmptyCredentialsError):
            login(credentials="   ")
        
        # Test 4: Valid format with colon
        with patch('ssky.login.SskySession') as mock_session_class:
            mock_session_class.return_value = mock_session
            
            result = login(credentials="user:pass")
            assert isinstance(result, ProfileList), "Should return ProfileList for valid credentials"
            
            # Verify correct parsing
            call_args = mock_session_class.call_args
            assert call_args.kwargs['handle'] == "user", "Handle should be parsed correctly"
            assert call_args.kwargs['password'] == "pass", "Password should be parsed correctly"
    
    def test_04_login_session_error_handling(self, login_environment):
        """Test error handling when SskySession raises exceptions"""
        
        # Test 1: LoginRequiredError from SskySession
        with patch('ssky.login.SskySession') as mock_session_class:
            import atproto_client
            mock_session_class.side_effect = atproto_client.exceptions.LoginRequiredError("Mock login required")
            
            with pytest.raises(AtProtocolSskyError):
                login(credentials="test:test")
        
        # Test 2: AtProtocolError from SskySession
        with patch('ssky.login.SskySession') as mock_session_class:
            import atproto_client
            mock_session_class.side_effect = atproto_client.exceptions.AtProtocolError("Mock auth failed")
            
            with pytest.raises(AtProtocolSskyError):
                login(credentials="test:test")
    
    def test_05_login_profile_availability_check(self, login_environment, mock_ssky_session):
        """Test profile availability check after login"""
        
        # Unpack mock objects
        mock_session, mock_client, mock_profile = mock_ssky_session
        
        # Test 1: Profile is None
        mock_session.profile.return_value = None
        
        with patch('ssky.login.SskySession') as mock_session_class:
            mock_session_class.return_value = mock_session
            
            with pytest.raises(ProfileUnavailableAfterLoginError):
                login(credentials="test:test")
        
        # Test 2: Profile has no DID
        mock_session, mock_client, mock_profile = create_mock_ssky_session()
        mock_profile.did = None
        
        with patch('ssky.login.SskySession') as mock_session_class:
            mock_session_class.return_value = mock_session
            
            with pytest.raises(ProfileUnavailableAfterLoginError):
                login(credentials="test:test")
        
        # Test 3: Profile missing DID attribute
        mock_session, mock_client, mock_profile = create_mock_ssky_session()
        del mock_profile.did  # Remove the attribute entirely
        
        with patch('ssky.login.SskySession') as mock_session_class:
            mock_session_class.return_value = mock_session
            
            with pytest.raises(ProfileUnavailableAfterLoginError):
                login(credentials="test:test")
    
    def test_06_login_no_credentials_available(self, login_environment):
        """Test login behavior when no credentials are available but valid session file exists"""
        
        # Temporarily remove SSKY_USER environment variable
        original_user = os.environ.get('SSKY_USER')
        if 'SSKY_USER' in os.environ:
            del os.environ['SSKY_USER']
        
        # Clear session state but keep session file (normal behavior)
        from ssky.ssky_session import SskySession
        SskySession.clear()
        
        try:
            # Test login without explicit credentials
            # Should succeed if valid session file exists
            result = login()
            assert isinstance(result, ProfileList), "Should return ProfileList when valid session file exists"
                
        finally:
            # Restore original environment variable
            if original_user:
                os.environ['SSKY_USER'] = original_user
    
    def test_07_login_no_credentials_no_session_file(self, login_environment):
        """Test login behavior when no credentials and no session file are available"""
        
        # Temporarily remove SSKY_USER environment variable
        original_user = os.environ.get('SSKY_USER')
        if 'SSKY_USER' in os.environ:
            del os.environ['SSKY_USER']
        
        # Clear session state
        from ssky.ssky_session import SskySession
        SskySession.clear()
        
        # Temporarily remove session file if it exists
        session_file = os.path.expanduser('~/.ssky')
        session_backup = None
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                session_backup = f.read()
            os.remove(session_file)
        
        try:
            # Test login without any credentials or session file
            with pytest.raises(AtProtocolSskyError):
                login()
        finally:
            # Restore original environment variable
            if original_user:
                os.environ['SSKY_USER'] = original_user
            
            # Restore session file if it existed
            if session_backup is not None:
                with open(session_file, 'w') as f:
                    f.write(session_backup)
