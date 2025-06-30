import os
import tempfile
import pytest
from unittest.mock import patch, Mock

from ssky.profile_list import ProfileList
from ssky.follow import follow
from ssky.unfollow import unfollow
from ssky.ssky_session import SskySession
from ssky.util import ErrorResult
from tests.common import create_mock_ssky_session, has_credentials

@pytest.fixture
def mock_follow_environment():
    """Setup test environment for follow/unfollow tests"""
    if not has_credentials():
        pytest.skip("No credentials available")
    
    # Create mock session for all follow/unfollow tests
    mock_session, mock_client, mock_profile = create_mock_ssky_session()
    
    # Set up proper mock responses for follow/unfollow functionality
    # Mock follow response
    mock_follow_response = Mock()
    mock_follow_response.uri = "at://test.user/app.bsky.graph.follow/test123"
    mock_client.follow.return_value = mock_follow_response
    
    # Mock unfollow response
    mock_client.unfollow.return_value = True
    
    # Mock profile response for follow functionality
    mock_profile_response = Mock()
    mock_profile_response.did = "did:plc:test123"
    mock_client.app.bsky.actor.get_profile.return_value = mock_profile_response
    
    # Mock follows response for unfollow functionality
    mock_follow = Mock()
    mock_follow.did = "did:plc:test123"
    mock_follow.handle = "test.bsky.social"
    mock_follow.viewer = Mock()
    mock_follow.viewer.following = "at://test.user/app.bsky.graph.follow/test123"
    
    mock_follows_response = Mock()
    mock_follows_response.follows = [mock_follow]
    mock_client.get_follows.return_value = mock_follows_response
    
    return mock_session, mock_client, mock_profile

class TestFollowUnfollowSequential:
    """Sequential follow/unfollow tests using mocked SskySession
    
    Strategy: 1 real follow/unfollow cycle + mocked tests for other scenarios
    This reduces API calls and avoids rate limits.
    """
    
    def test_01_real_follow_unfollow_by_handle(self):
        """Real API test - follow and unfollow by handle (only real API test in this file)"""
        # Skip if no credentials available
        if not has_credentials():
            pytest.skip("SSKY_USER environment variable not set")
        
        # This test uses real API calls - no mocking
        try:
            handle = os.environ.get('SSKY_TEST_HANDLE', 'test.bsky.social')
            
            # Follow
            follow_result = follow(handle)
            assert isinstance(follow_result, ProfileList), "Follow should return ProfileList"
            
            # Wait a bit before unfollowing
            import time
            time.sleep(5)
            
            # Unfollow
            unfollow_result = unfollow(handle)
            assert isinstance(unfollow_result, ProfileList), "Unfollow should return ProfileList"
            
        finally:
            SskySession.clear()
    
    def test_02_follow_by_did_with_mock(self, mock_follow_environment):
        """Test follow by DID using mocked session"""
        mock_session, mock_client, mock_profile = mock_follow_environment
        
        with patch('ssky.follow.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            did = os.environ.get('SSKY_TEST_DID', 'did:plc:test123')
            result = follow(did)
            
            assert isinstance(result, ProfileList), "Follow should return ProfileList"
    
    def test_03_unfollow_by_did_with_mock(self, mock_follow_environment):
        """Test unfollow by DID using mocked session"""
        mock_session, mock_client, mock_profile = mock_follow_environment
        
        # Update mock to match the test DID
        mock_follow = Mock()
        mock_follow.did = os.environ.get('SSKY_TEST_DID', 'did:plc:test123')
        mock_follow.handle = "test.bsky.social"
        mock_follow.viewer = Mock()
        mock_follow.viewer.following = "at://test.user/app.bsky.graph.follow/test123"
        
        mock_follows_response = Mock()
        mock_follows_response.follows = [mock_follow]
        mock_client.get_follows.return_value = mock_follows_response
        
        with patch('ssky.unfollow.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            did = os.environ.get('SSKY_TEST_DID', 'did:plc:test123')
            result = unfollow(did)
            
            assert isinstance(result, ProfileList), "Unfollow should return ProfileList"
    
    def test_04_unfollow_not_following_user(self, mock_follow_environment):
        """Test unfollow user that is not being followed"""
        mock_session, mock_client, mock_profile = mock_follow_environment
        
        # Mock follows response with empty list (not following anyone)
        mock_follows_response = Mock()
        mock_follows_response.follows = []
        mock_client.get_follows.return_value = mock_follows_response
        
        with patch('ssky.unfollow.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            handle = os.environ.get('SSKY_TEST_HANDLE', 'test.bsky.social')
            result = unfollow(handle)
            
            assert isinstance(result, ErrorResult), "Unfollow should return ErrorResult when not following"
    
    def test_05_follow_invalid_user(self, mock_follow_environment):
        """Test follow with invalid user"""
        mock_session, mock_client, mock_profile = mock_follow_environment
        
        # Mock get_profile to raise exception for invalid user
        import atproto_client
        mock_client.get_profile.side_effect = atproto_client.exceptions.AtProtocolError("User not found")
        
        with patch('ssky.follow.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            invalid_did = os.environ.get('SSKY_TEST_INVALID_DID', 'did:plc:invalid123')
            result = follow(invalid_did)
            
            assert isinstance(result, ErrorResult), "Follow should return ErrorResult for invalid user"
    
    def test_06_unfollow_invalid_user(self, mock_follow_environment):
        """Test unfollow with invalid user"""
        mock_session, mock_client, mock_profile = mock_follow_environment
        
        # Mock get_follows to raise exception for invalid user
        import atproto_client
        mock_client.get_follows.side_effect = atproto_client.exceptions.AtProtocolError("User not found")
        
        with patch('ssky.unfollow.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            invalid_did = os.environ.get('SSKY_TEST_INVALID_DID', 'did:plc:invalid123')
            result = unfollow(invalid_did)
            
            assert isinstance(result, ErrorResult), "Unfollow should return ErrorResult for invalid user"
    
    def test_07_follow_unfollow_error_scenarios(self):
        """Test error handling scenarios"""
        # Test 1: No session available for follow
        with patch('ssky.follow.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = None
            
            result = follow("test.bsky.social")
            assert isinstance(result, ErrorResult), "Follow should return ErrorResult when no session available"
            assert result.http_code == 401, "Should return 401 error code"
        
        # Test 2: No session available for unfollow
        with patch('ssky.unfollow.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = None
            
            result = unfollow("test.bsky.social")
            assert isinstance(result, ErrorResult), "Unfollow should return ErrorResult when no session available"
            assert result.http_code == 401, "Should return 401 error code"
        
        # Test 3: Empty identifier for follow
        result = follow("")
        assert isinstance(result, ErrorResult), "Follow should return ErrorResult with empty identifier"
        
        # Test 4: Empty identifier for unfollow
        result = unfollow("")
        assert isinstance(result, ErrorResult), "Unfollow should return ErrorResult with empty identifier"
    
    def test_08_follow_unfollow_with_json_format(self, mock_follow_environment):
        """Test follow/unfollow with JSON format output"""
        mock_session, mock_client, mock_profile = mock_follow_environment
        
        # Test follow with JSON format
        with patch('ssky.follow.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            handle = os.environ.get('SSKY_TEST_HANDLE', 'test.bsky.social')
            result = follow(handle, format='json')
            
            assert isinstance(result, ProfileList), "Follow should return ProfileList with JSON format"
        
        # Test unfollow with JSON format
        # Update mock to match the test handle
        handle = os.environ.get('SSKY_TEST_HANDLE', 'test.bsky.social')
        mock_follow = Mock()
        mock_follow.did = "did:plc:test123"
        mock_follow.handle = handle  # Use the actual test handle
        mock_follow.viewer = Mock()
        mock_follow.viewer.following = "at://test.user/app.bsky.graph.follow/test123"
        
        mock_follows_response = Mock()
        mock_follows_response.follows = [mock_follow]
        mock_client.get_follows.return_value = mock_follows_response
        
        with patch('ssky.unfollow.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            result = unfollow(handle, format='json')
            
            assert isinstance(result, ProfileList), "Unfollow should return ProfileList with JSON format"