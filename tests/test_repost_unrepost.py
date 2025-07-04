import os
import tempfile
import pytest
from unittest.mock import patch, Mock
import time

from ssky.post_data_list import PostDataList
from ssky.repost import repost
from ssky.unrepost import unrepost
from ssky.ssky_session import SskySession
from ssky.util import disjoin_uri_cid
from ssky.result import ErrorResult
from tests.common import create_mock_ssky_session, has_credentials

@pytest.fixture
def mock_repost_environment():
    """Setup test environment for repost/unrepost tests"""
    if not has_credentials():
        pytest.skip("No credentials available")
    
    # Create mock session for all repost/unrepost tests
    mock_session, mock_client, mock_profile = create_mock_ssky_session()
    
    # Set up proper mock responses for repost/unrepost functionality
    # Mock repost response
    mock_repost_response = Mock()
    mock_repost_response.uri = "at://test.user/app.bsky.feed.repost/test123"
    mock_repost_response.cid = "repostcid123"
    mock_client.repost.return_value = mock_repost_response
    
    # Mock unrepost response
    mock_client.unrepost.return_value = True
    
    # Mock original post with repost viewer info for unrepost functionality
    mock_viewer = Mock()
    mock_viewer.repost = "at://test.user/app.bsky.feed.repost/test123"
    
    # Get actual URI and CID from environment for proper mock setup
    uri_cid = os.environ.get('SSKY_TEST_URI_CID', 'at://test.user/app.bsky.feed.post/test123::testcid123')
    actual_uri, actual_cid = disjoin_uri_cid(uri_cid)
    
    mock_original_post = Mock()
    mock_original_post.uri = actual_uri
    mock_original_post.cid = actual_cid
    mock_original_post.viewer = mock_viewer
    mock_original_post.__str__ = lambda: mock_original_post.uri
    
    # Mock posts response
    mock_posts_response = Mock()
    mock_posts_response.posts = [mock_original_post]
    mock_client.get_posts.return_value = mock_posts_response
    
    # Mock reposts response for unrepost functionality
    mock_repost_item = Mock()
    mock_repost_item.uri = "at://test.user/app.bsky.feed.repost/test123"
    mock_repost_item.cid = "repostcid123"
    mock_repost_item.author = Mock()
    mock_repost_item.author.did = "did:plc:test123"  # Match the session user DID
    
    mock_reposts_response = Mock()
    mock_reposts_response.reposts = [mock_repost_item]
    mock_client.get_reposts.return_value = mock_reposts_response
    
    # Mock delete_repost response
    mock_client.delete_repost.return_value = True
    
    # Mock session user DID for unrepost matching
    mock_client.me = Mock()
    mock_client.me.did = "did:plc:test123"
    
    return mock_session, mock_client, mock_profile

class TestRepostUnrepostSequential:
    """Sequential repost/unrepost tests using mocked SskySession
    
    Strategy: 1 real repost/unrepost cycle + mocked tests for other scenarios
    This reduces API calls and avoids rate limits.
    """
    
    def test_01_real_repost_unrepost_by_uri(self):
        """Real API test - repost and unrepost by URI (only real API test in this file)"""
        # Skip if no credentials available
        if not has_credentials():
            pytest.skip("SSKY_USER environment variable not set")
        
        # This test uses real API calls - no mocking
        try:
            uri = os.environ.get('SSKY_TEST_URI', 'at://test.user/app.bsky.feed.post/test123')
            
            # Repost
            repost_result = repost(uri)
            assert isinstance(repost_result, PostDataList), "Repost should return PostDataList"
            
            # Wait a bit before unreposting
            time.sleep(5)
            
            # Unrepost
            unrepost_result = unrepost(uri)
            assert isinstance(unrepost_result, PostDataList), "Unrepost should return PostDataList"
            
        finally:
            SskySession.clear()
    
    def test_02_repost_by_uri_cid_with_mock(self, mock_repost_environment):
        """Test repost by URI+CID using mocked session"""
        mock_session, mock_client, mock_profile = mock_repost_environment
        
        with patch('ssky.repost.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            uri_cid = os.environ.get('SSKY_TEST_URI_CID', 'at://test.user/app.bsky.feed.post/test123::testcid123')
            result = repost(uri_cid)
            
            assert isinstance(result, PostDataList), "Repost should return PostDataList"
    
    def test_03_unrepost_by_uri_cid_with_mock(self, mock_repost_environment):
        """Test unrepost by URI+CID using mocked session"""
        mock_session, mock_client, mock_profile = mock_repost_environment
        
        with patch('ssky.unrepost.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            uri_cid = os.environ.get('SSKY_TEST_URI_CID', 'at://test.user/app.bsky.feed.post/test123::testcid123')
            result = unrepost(uri_cid)
            
            assert isinstance(result, PostDataList), "Unrepost should return PostDataList"
    
    def test_04_unrepost_not_reposted_uri(self, mock_repost_environment):
        """Test unrepost URI that was not reposted"""
        mock_session, mock_client, mock_profile = mock_repost_environment
        
        # Mock post without repost viewer info (not reposted)
        mock_original_post = Mock()
        mock_original_post.uri = "at://test.user/app.bsky.feed.post/test123"
        mock_original_post.cid = "testcid123"
        mock_original_post.viewer = Mock()
        mock_original_post.viewer.repost = None  # Not reposted
        mock_original_post.__str__ = lambda: mock_original_post.uri
        
        # Override the get_posts response to return the post without repost info
        mock_posts_response = Mock()
        mock_posts_response.posts = [mock_original_post]
        mock_client.get_posts.return_value = mock_posts_response
        
        with patch('ssky.unrepost.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            uri = os.environ.get('SSKY_TEST_URI', 'at://test.user/app.bsky.feed.post/test123')
            
            from ssky.result import NotFoundError
            with pytest.raises(NotFoundError):
                unrepost(uri)
    
    def test_05_repost_invalid_uri(self, mock_repost_environment):
        """Test repost with invalid URI"""
        mock_session, mock_client, mock_profile = mock_repost_environment
        
        # Mock repost to raise exception for invalid URI
        import atproto_client
        mock_client.repost.side_effect = atproto_client.exceptions.AtProtocolError("Post not found")
        
        with patch('ssky.repost.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            invalid_uri = os.environ.get('SSKY_TEST_INVALID_URI', 'at://invalid/uri')
            
            from ssky.result import AtProtocolSskyError
            with pytest.raises(AtProtocolSskyError):
                repost(invalid_uri)
    
    def test_06_unrepost_invalid_uri(self, mock_repost_environment):
        """Test unrepost with invalid URI"""
        mock_session, mock_client, mock_profile = mock_repost_environment
        
        # Mock get_posts to return empty posts list for invalid URI
        mock_empty_posts_response = Mock()
        mock_empty_posts_response.posts = []
        mock_client.get_posts.return_value = mock_empty_posts_response
        
        with patch('ssky.unrepost.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            invalid_uri = os.environ.get('SSKY_TEST_INVALID_URI', 'at://invalid/uri')
            
            from ssky.result import NotFoundError
            with pytest.raises(NotFoundError):
                unrepost(invalid_uri)
    
    def test_07_repost_unrepost_error_scenarios(self):
        """Test error handling scenarios"""
        # Test 1: No session available for repost
        from ssky.result import SessionError
        with patch('ssky.repost.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = None
            
            with pytest.raises(SessionError):
                repost("at://test.user/app.bsky.feed.post/test123")
        
        # Test 2: No session available for unrepost
        with patch('ssky.unrepost.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = None
            
            with pytest.raises(SessionError):
                unrepost("at://test.user/app.bsky.feed.post/test123")
        
        # Test 3: Empty URI for repost
        from ssky.result import InvalidUriError
        with pytest.raises(InvalidUriError):
            repost("")
        
        # Test 4: Empty URI for unrepost
        with pytest.raises(InvalidUriError):
            unrepost("")
    
    def test_08_repost_unrepost_with_json_format(self, mock_repost_environment):
        """Test repost/unrepost with JSON format output"""
        mock_session, mock_client, mock_profile = mock_repost_environment
        
        # Test repost with JSON format
        with patch('ssky.repost.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            uri = os.environ.get('SSKY_TEST_URI', 'at://test.user/app.bsky.feed.post/test123')
            result = repost(uri, format='json')
            
            assert isinstance(result, PostDataList), "Repost should return PostDataList with JSON format"
        
        # Test unrepost with JSON format
        with patch('ssky.unrepost.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            uri = os.environ.get('SSKY_TEST_URI', 'at://test.user/app.bsky.feed.post/test123')
            result = unrepost(uri, format='json')
            
            assert isinstance(result, PostDataList), "Unrepost should return PostDataList with JSON format"