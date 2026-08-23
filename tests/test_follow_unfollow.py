import os
import tempfile
import pytest
from unittest.mock import patch, Mock
import time

from ssky.profile_list import ProfileList
from ssky.follow import follow
from ssky.unfollow import unfollow
from ssky.ssky_session import SskySession, ssky_client
from ssky.result import ErrorResult
from tests.common import create_mock_ssky_session, has_credentials, read_test_config

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
    
    @pytest.mark.real_api
    @pytest.mark.write_api
    def test_01_real_follow_unfollow_by_handle(self, require_test_account):
        """Real API test - follow and unfollow by handle (only real API test in this file)

        Two constraints the target has to satisfy. The unfollow at the end is
        unconditional, so the test account must not already follow the target — it
        would delete a relationship this test did not create. And the target must be
        an account under your control, because it receives a follow notification on
        every run; it used to default to bsky.app.
        """
        target = read_test_config('SSKY_TEST_FOLLOW_TARGET')
        if not target:
            pytest.skip(
                "SSKY_TEST_FOLLOW_TARGET is not set. Point it at an account you control; "
                "this test really follows and then unfollows it."
            )

        # This test uses real API calls - no mocking
        try:
            client = ssky_client()
            before = client.get_profile(actor=target)
            if before.viewer is not None and before.viewer.following is not None:
                pytest.skip(
                    f"The test account already follows {target}; the unfollow step would "
                    f"destroy a relationship this test did not create."
                )

            # Follow
            follow_result = follow(target)
            assert isinstance(follow_result, ProfileList), "Follow should return ProfileList"

            # Wait a bit before unfollowing
            time.sleep(5)

            # Unfollow
            unfollow_result = unfollow(target)
            assert isinstance(unfollow_result, ProfileList), "Unfollow should return ProfileList"

            # Graph records are eventually consistent, the same way post availability
            # is: a read taken right after the unfollow can still show the record.
            # Poll instead of asserting once, or this test is flaky by construction.
            deadline = time.time() + 30
            while True:
                after = client.get_profile(actor=target)
                if after.viewer is None or after.viewer.following is None:
                    break
                assert time.time() < deadline, \
                    f"Follow record still present 30s after unfollow: {after.viewer.following}"
                time.sleep(2)

        finally:
            SskySession.clear()
    
    @pytest.mark.needs_session
    def test_02_follow_by_did_with_mock(self, mock_follow_environment):
        """Test follow by DID using mocked session"""
        mock_session, mock_client, mock_profile = mock_follow_environment
        
        with patch('ssky.follow.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            did = os.environ.get('SSKY_TEST_DID', 'did:plc:test123')
            result = follow(did)
            
            assert isinstance(result, ProfileList), "Follow should return ProfileList"
    
    @pytest.mark.needs_session
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
    
    @pytest.mark.needs_session
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
            
            from ssky.result import NotFoundError
            with pytest.raises(NotFoundError):
                unfollow(handle)
    
    @pytest.mark.needs_session
    def test_05_follow_invalid_user(self, mock_follow_environment):
        """Test follow with invalid user"""
        mock_session, mock_client, mock_profile = mock_follow_environment
        
        # Mock follow to raise exception for invalid user
        import atproto_client
        mock_client.follow.side_effect = atproto_client.exceptions.AtProtocolError("User not found")
        
        with patch('ssky.follow.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            invalid_did = os.environ.get('SSKY_TEST_INVALID_DID', 'did:plc:invalid123')
            
            from ssky.result import AtProtocolSskyError
            with pytest.raises(AtProtocolSskyError):
                follow(invalid_did)
    
    @pytest.mark.needs_session
    def test_06_unfollow_invalid_user(self, mock_follow_environment):
        """Test unfollow with invalid user"""
        mock_session, mock_client, mock_profile = mock_follow_environment
        
        # Mock get_follows to raise exception for invalid user
        import atproto_client
        mock_client.get_follows.side_effect = atproto_client.exceptions.AtProtocolError("User not found")
        
        with patch('ssky.unfollow.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            invalid_did = os.environ.get('SSKY_TEST_INVALID_DID', 'did:plc:invalid123')
            
            from ssky.result import AtProtocolSskyError
            with pytest.raises(AtProtocolSskyError):
                unfollow(invalid_did)
    
    @pytest.mark.needs_session
    def test_07_follow_unfollow_error_scenarios(self):
        """Test error handling scenarios"""
        # Test 1: No session available for follow
        from ssky.result import SessionError
        with patch('ssky.follow.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = None
            
            with pytest.raises(SessionError):
                follow("test.bsky.social")
        
        # Test 2: No session available for unfollow
        with patch('ssky.unfollow.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = None
            
            with pytest.raises(SessionError):
                unfollow("test.bsky.social")
        
        # Test 3: Empty identifier for follow
        from ssky.result import InvalidActorError
        with pytest.raises(InvalidActorError):
            follow("")
        
        # Test 4: Empty identifier for unfollow
        with pytest.raises(InvalidActorError):
            unfollow("")
    
    @pytest.mark.needs_session
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
        
        # Mock expand_actor to return a consistent DID
        test_did = "did:plc:test123"
        
        mock_follow = Mock()
        mock_follow.did = test_did
        mock_follow.handle = handle
        mock_follow.viewer = Mock()
        mock_follow.viewer.following = "at://test.user/app.bsky.graph.follow/test123"
        
        mock_follows_response = Mock()
        mock_follows_response.follows = [mock_follow]
        mock_client.get_follows.return_value = mock_follows_response
        
        with patch('ssky.unfollow.ssky_client') as mock_ssky_client, \
             patch('ssky.unfollow.expand_actor') as mock_expand_actor:
            mock_ssky_client.return_value = mock_client
            mock_expand_actor.return_value = test_did  # Make sure expand_actor returns the same DID
            
            result = unfollow(handle, format='json')
            
            assert isinstance(result, ProfileList), "Unfollow should return ProfileList with JSON format"