import os
import pytest
from unittest.mock import Mock, patch

from ssky.get import get
from ssky.post_data_list import PostDataList
from ssky.ssky_session import SskySession
from ssky.result import ErrorResult
from tests.common import create_mock_ssky_session, has_credentials

@pytest.fixture
def mock_get_environment():
    """Setup test environment for get tests"""
    if not has_credentials():
        pytest.skip("No credentials available")
    
    # Create mock session for all get tests
    mock_session, mock_client, mock_profile = create_mock_ssky_session()
    
    # Set up proper mock responses for get functionality
    # Mock post for posts response
    mock_post = Mock()
    mock_post.uri = "at://test.user/app.bsky.feed.post/test123"
    mock_post.cid = "testcid123"
    mock_post.author = Mock()
    mock_post.author.did = "did:plc:test123"
    mock_post.author.handle = "test.bsky.social"
    mock_post.record = Mock()
    mock_post.record.text = "Test post content"
    
    # Mock feed post for feed responses
    mock_feed_post = Mock()
    mock_feed_post.post = mock_post
    
    # Set up timeline response
    mock_timeline_response = Mock()
    mock_timeline_response.feed = [mock_feed_post]
    mock_client.get_timeline.return_value = mock_timeline_response
    
    # Set up author feed response
    mock_author_feed_response = Mock()
    mock_author_feed_response.feed = [mock_feed_post]
    mock_client.get_author_feed.return_value = mock_author_feed_response
    
    # Set up posts response
    mock_posts_response = Mock()
    mock_posts_response.posts = [mock_post]
    mock_client.get_posts.return_value = mock_posts_response
    
    return mock_session, mock_client, mock_profile

class TestGetSequential:
    """Sequential tests for get functionality using mocked SskySession"""
    
    def test_01_real_get_timeline(self):
        """Real API test - get timeline (only real API test in this file)"""
        # Skip if no credentials available
        if not has_credentials():
            pytest.skip("SSKY_USER environment variable not set")
        
        # This test uses real API calls - no mocking
        try:
            result = get(target=None)
            assert isinstance(result, PostDataList), "Get timeline should return PostDataList"
        finally:
            SskySession.clear()
    
    def test_02_get_myself(self, mock_get_environment):
        """Test get my own posts using mocked session"""
        mock_session, mock_client, mock_profile = mock_get_environment
        
        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            result = get(target='myself')
            assert isinstance(result, PostDataList), "Get myself should return PostDataList"
    
    def test_03_get_with_actor_handle(self, mock_get_environment):
        """Test get posts by actor handle"""
        mock_session, mock_client, mock_profile = mock_get_environment
        
        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            handle = os.environ.get('SSKY_TEST_HANDLE', 'test.bsky.social')
            result = get(target=handle)
            
            assert isinstance(result, PostDataList), "Get by handle should return PostDataList"
    
    def test_04_get_with_actor_did(self, mock_get_environment):
        """Test get posts by actor DID"""
        mock_session, mock_client, mock_profile = mock_get_environment
        
        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            did = os.environ.get('SSKY_TEST_DID', 'did:plc:test123')
            result = get(target=did)
            
            assert isinstance(result, PostDataList), "Get by DID should return PostDataList"
    
    def test_05_get_with_at_uri(self, mock_get_environment):
        """Test get specific post by AT URI"""
        mock_session, mock_client, mock_profile = mock_get_environment
        
        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            uri = os.environ.get('SSKY_TEST_URI', 'at://test.user/app.bsky.feed.post/test123')
            result = get(target=uri)
            
            assert isinstance(result, PostDataList), "Get by URI should return PostDataList"
    
    def test_06_get_with_at_uri_cid(self, mock_get_environment):
        """Test get specific post by AT URI with CID"""
        mock_session, mock_client, mock_profile = mock_get_environment
        
        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            uri_cid = os.environ.get('SSKY_TEST_URI_CID', 'at://test.user/app.bsky.feed.post/test123|testcid123')
            result = get(target=uri_cid)
            
            assert isinstance(result, PostDataList), "Get by URI+CID should return PostDataList"
    
    def test_07_get_invalid_targets(self, mock_get_environment):
        """Test get with invalid targets"""
        mock_session, mock_client, mock_profile = mock_get_environment
        
        # Mock exception for invalid targets
        import atproto_client
        mock_client.get_author_feed.side_effect = atproto_client.exceptions.AtProtocolError("Not found")
        mock_client.get_posts.side_effect = atproto_client.exceptions.AtProtocolError("Not found")
        
        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            from ssky.result import InvalidActorError, AtProtocolSskyError
            
            # Test invalid handle - expand_actor returns None, so InvalidActorError
            with patch('ssky.get.expand_actor') as mock_expand_actor:
                mock_expand_actor.return_value = None
                invalid_handle = os.environ.get('SSKY_TEST_INVALID_HANDLE', 'invalid.handle.test')
                with pytest.raises(InvalidActorError):
                    get(target=invalid_handle)
            
            # Test invalid DID - goes directly to get_author_feed, so AtProtocolSskyError
            invalid_did = os.environ.get('SSKY_TEST_INVALID_DID', 'did:plc:invalid123')
            with pytest.raises(AtProtocolSskyError):
                get(target=invalid_did)
            
            # Test invalid URI - should raise AtProtocolSskyError from API call
            invalid_uri = os.environ.get('SSKY_TEST_INVALID_URI', 'at://invalid/uri')
            with pytest.raises(AtProtocolSskyError):
                get(target=invalid_uri)
            
            # Test invalid URI+CID - should raise AtProtocolSskyError from API call
            invalid_uri_cid = os.environ.get('SSKY_TEST_INVALID_URI_CID', 'at://invalid/uri|invalidcid')
            with pytest.raises(AtProtocolSskyError):
                get(target=invalid_uri_cid)
    
    def test_08_get_error_scenarios(self):
        """Test error handling scenarios"""
        # Test: No session available
        from ssky.result import SessionError
        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = None
            
            with pytest.raises(SessionError):
                get(param=None)
    
    def test_09_get_with_json_format(self, mock_get_environment):
        """Test get with JSON format output"""
        mock_session, mock_client, mock_profile = mock_get_environment
        
        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client

            result = get(param=None, format='json')
            assert isinstance(result, PostDataList), "Get with JSON format should return PostDataList"