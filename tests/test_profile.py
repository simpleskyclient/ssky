import os
import tempfile
import pytest
from unittest.mock import patch, Mock

from ssky.profile import profile
from ssky.profile_list import ProfileList
from ssky.util import ErrorResult
from tests.common import (
    create_mock_ssky_session, has_credentials
)

@pytest.fixture
def mock_profile_environment():
    """Setup test environment for profile tests"""
    if not has_credentials():
        pytest.skip("No credentials available")
    
    # Create mock session for all profile tests
    mock_session, mock_client, mock_profile = create_mock_ssky_session()
    return mock_session, mock_client, mock_profile

@pytest.fixture
def mock_profile_response():
    """Create a standard mock profile response"""
    mock_response = Mock()
    mock_response.did = "did:plc:test123"
    mock_response.handle = "test.bsky.social"
    mock_response.display_name = "Test User"
    mock_response.description = "Test description"
    mock_response.avatar = "https://example.com/avatar.jpg"
    mock_response.banner = None
    mock_response.followers_count = 100
    mock_response.follows_count = 50
    mock_response.posts_count = 25
    mock_response.created_at = "2023-01-01T00:00:00.000Z"
    mock_response.indexed_at = "2023-01-01T01:00:00.000Z"
    return mock_response

class TestProfileSequential:
    """Sequential profile tests using mocked SskySession
    
    Strategy: Mock SskySession to avoid API calls while testing profile function logic
    """
    
    def test_01_profile_by_handle(self, mock_profile_environment, mock_profile_response):
        """Test get profile by handle using mocked session"""
        
        mock_session, mock_client, mock_profile = mock_profile_environment
        
        # Set up mock client response
        mock_client.get_profile.return_value = mock_profile_response
        
        with patch('ssky.profile.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            handle = "test.bsky.social"
            result = profile(handle)
            
            assert isinstance(result, ProfileList), "Profile by handle should return ProfileList"
            
            # Verify ssky_client was called
            mock_ssky_client.assert_called_once()
            
            # Verify client.get_profile was called with correct parameter
            mock_client.get_profile.assert_called_once()
            
    
    def test_02_profile_by_did(self, mock_profile_environment, mock_profile_response):
        """Test get profile by DID using mocked session"""
        
        mock_session, mock_client, mock_profile = mock_profile_environment
        
        # Set up mock client response
        mock_client.get_profile.return_value = mock_profile_response
        
        with patch('ssky.profile.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            did = os.environ.get('SSKY_TEST_DID', 'did:plc:test123')
            result = profile(did)
            
            assert isinstance(result, ProfileList), "Profile by DID should return ProfileList"
            
            # Verify ssky_client was called
            mock_ssky_client.assert_called_once()
            
            # Verify client.get_profile was called
            mock_client.get_profile.assert_called_once()
        
    
    def test_03_profile_invalid_handle(self, mock_profile_environment):
        """Test get profile with invalid handle"""
        
        mock_session, mock_client, mock_profile = mock_profile_environment
        
        # Mock exception for invalid handle
        import atproto_client
        mock_client.get_profile.side_effect = atproto_client.exceptions.AtProtocolError("Profile not found")
        
        with patch('ssky.profile.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            invalid_handle = os.environ.get('SSKY_TEST_INVALID_HANDLE', 'invalid.handle.test')
            result = profile(invalid_handle)
            
            assert isinstance(result, ErrorResult), "Profile with invalid handle should return ErrorResult"
        
    
    def test_04_profile_invalid_did(self, mock_profile_environment):
        """Test get profile with invalid DID"""
        
        mock_session, mock_client, mock_profile = mock_profile_environment
        
        # Mock exception for invalid DID
        import atproto_client
        mock_client.get_profile.side_effect = atproto_client.exceptions.AtProtocolError("Profile not found")
        
        with patch('ssky.profile.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            invalid_did = os.environ.get('SSKY_TEST_INVALID_DID', 'did:plc:invalid123')
            result = profile(invalid_did)
            
            assert isinstance(result, ErrorResult), "Profile with invalid DID should return ErrorResult"
        
    
    def test_05_profile_error_scenarios(self):
        """Test error handling scenarios"""
        
        # Test 1: No session available (ssky_client returns None)
        with patch('ssky.profile.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = None
            
            result = profile("test.bsky.social")
            assert isinstance(result, ErrorResult), "Profile should return ErrorResult when no session available"
            assert result.http_code == 401, "Profile should return 401 error code"
        
        # Test 2: Empty identifier
        result = profile("")
        assert isinstance(result, ErrorResult), "Profile should return ErrorResult with empty identifier"
        
    
    def test_06_profile_with_json_format(self, mock_profile_environment, mock_profile_response):
        """Test profile with JSON format output"""
        
        mock_session, mock_client, mock_profile = mock_profile_environment
        
        # Set up mock client response
        mock_client.get_profile.return_value = mock_profile_response
        
        with patch('ssky.profile.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            handle = os.environ.get('SSKY_TEST_HANDLE', 'test.bsky.social')
            result = profile(handle, format='json')
            
            assert isinstance(result, ProfileList), "Profile should return ProfileList with JSON format"
        
    
    def test_07_profile_login_required_error(self):
        """Test profile when LoginRequiredError is raised"""
        
        # Mock ssky_client to raise LoginRequiredError
        import atproto_client
        
        with patch('ssky.profile.ssky_client') as mock_ssky_client:
            mock_ssky_client.side_effect = atproto_client.exceptions.LoginRequiredError("Login required")
            
            result = profile("test.bsky.social")
            assert isinstance(result, ErrorResult), "Profile should return ErrorResult on LoginRequiredError"
            assert result.http_code == 401, "Profile should return 401 error code"
        
