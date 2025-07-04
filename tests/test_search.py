import os
import tempfile
import pytest
from unittest.mock import patch, Mock

from ssky.post_data_list import PostDataList
from ssky.search import search
from ssky.ssky_session import SskySession
from ssky.result import ErrorResult
from tests.common import create_mock_ssky_session, has_credentials

@pytest.fixture
def mock_search_environment():
    """Setup test environment for search tests"""
    if not has_credentials():
        pytest.skip("No credentials available")
    
    # Create mock session for all search tests
    mock_session, mock_client, mock_profile = create_mock_ssky_session()
    
    # Set up proper mock responses for search functionality
    # Mock search post
    mock_post = Mock()
    mock_post.uri = "at://test.user/app.bsky.feed.post/test123"
    mock_post.cid = "testcid123"
    mock_post.__str__ = lambda: mock_post.uri
    
    # Add required attributes for PostDataList
    mock_author = Mock()
    mock_author.did = "did:plc:test123"
    mock_author.handle = "test.bsky.social"
    mock_author.display_name = "Test User"
    mock_author.avatar = "https://example.com/avatar.jpg"
    mock_post.author = mock_author
    
    mock_record = Mock()
    mock_record.text = "Test post content"
    mock_record.created_at = "2023-01-01T00:00:00.000Z"
    mock_record.facets = None
    mock_post.record = mock_record
    
    mock_post.indexed_at = "2023-01-01T01:00:00.000Z"
    mock_post.reply_count = 0
    mock_post.repost_count = 0
    mock_post.like_count = 0
    mock_post.viewer = None
    
    # Set up search response
    mock_search_response = Mock()
    mock_search_response.posts = [mock_post]
    mock_client.app.bsky.feed.search_posts.return_value = mock_search_response
    
    return mock_session, mock_client, mock_profile

class TestSearchSequential:
    """Sequential search tests using mocked SskySession
    
    Strategy: 1 real search + mocked tests for other scenarios
    This reduces API calls and avoids rate limits.
    """
    
    def test_01_real_search_basic(self):
        """Real API test - basic search functionality (only real API test in this file)"""
        # Skip if no credentials available
        if not has_credentials():
            pytest.skip("SSKY_USER environment variable not set")
        
        # This test uses real API calls - no mocking
        try:
            query = os.environ.get('SSKY_TEST_Q', 'test')
            result = search(query)
            assert isinstance(result, PostDataList), "Search should return PostDataList"
        finally:
            SskySession.clear()
    
    def test_02_search_with_limit(self, mock_search_environment):
        """Test search with limit using mocked session"""
        mock_session, mock_client, mock_profile = mock_search_environment
        
        # Mock search response with limited results
        limit = int(os.environ.get('SSKY_TEST_LIMIT', '1'))  # Default to 1 for predictable testing
        mock_posts = []
        
        for i in range(limit):
            mock_post = Mock()
            mock_post.uri = f"at://test.user/app.bsky.feed.post/test{i}"
            mock_post.cid = f"testcid{i}"
            mock_post.__str__ = lambda: mock_post.uri
            
            # Add required attributes for PostDataList
            mock_author = Mock()
            mock_author.did = f"did:plc:test{i}"
            mock_author.handle = f"test{i}.bsky.social"
            mock_author.display_name = f"Test User {i}"
            mock_author.avatar = "https://example.com/avatar.jpg"
            mock_post.author = mock_author
            
            mock_record = Mock()
            mock_record.text = f"Test post {i}"
            mock_record.created_at = "2023-01-01T00:00:00.000Z"
            mock_record.facets = None
            mock_post.record = mock_record
            
            mock_post.indexed_at = "2023-01-01T01:00:00.000Z"
            mock_post.reply_count = 0
            mock_post.repost_count = 0
            mock_post.like_count = 0
            mock_post.viewer = None
            
            mock_posts.append(mock_post)
        
        mock_search_response = Mock()
        mock_search_response.posts = mock_posts
        mock_client.app.bsky.feed.search_posts.return_value = mock_search_response
        
        with patch('ssky.search.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            query = os.environ.get('SSKY_TEST_Q', 'test')
            limit = int(os.environ.get('SSKY_TEST_LIMIT', '1'))  # Use same default as above
            result = search(query, limit=limit)
            
            assert isinstance(result, PostDataList), "Search should return PostDataList"
            assert len(result) == limit, f"Should return exactly {limit} results"
    
    def test_03_search_with_no_results(self, mock_search_environment):
        """Test search with query that returns no results"""
        mock_session, mock_client, mock_profile = mock_search_environment
        
        # Mock search response with no results
        mock_search_response = Mock()
        mock_search_response.posts = []
        mock_client.app.bsky.feed.search_posts.return_value = mock_search_response
        
        with patch('ssky.search.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            query = os.environ.get('SSKY_TEST_Q_WITH_NO_RESULTS', 'nonexistentquerythatreturnsnothing123')
            result = search(query)
            
            assert isinstance(result, PostDataList), "Search should return PostDataList even with no results"
            assert len(result) == 0, "Should return empty results"
    
    def test_04_search_with_actor_handle(self, mock_search_environment):
        """Test search with actor handle filter"""
        mock_session, mock_client, mock_profile = mock_search_environment
        
        with patch('ssky.search.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            query = os.environ.get('SSKY_TEST_Q', 'test')
            actor = os.environ.get('SSKY_TEST_USER_HANDLE', 'test.bsky.social')
            result = search(query, actor=actor)
            
            assert isinstance(result, PostDataList), "Search should return PostDataList"
    
    def test_05_search_with_actor_did(self, mock_search_environment):
        """Test search with actor DID filter"""
        mock_session, mock_client, mock_profile = mock_search_environment
        
        with patch('ssky.search.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            query = os.environ.get('SSKY_TEST_Q', 'test')
            actor = os.environ.get('SSKY_TEST_DID', 'did:plc:test123')
            result = search(query, actor=actor)
            
            assert isinstance(result, PostDataList), "Search should return PostDataList"
    
    def test_06_search_with_time_period(self, mock_search_environment):
        """Test search with time period filters"""
        mock_session, mock_client, mock_profile = mock_search_environment
        
        with patch('ssky.search.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            query = os.environ.get('SSKY_TEST_Q', 'test')
            since = os.environ.get('SSKY_TEST_SINCE', '2023-01-01T00:00:00Z')
            until = os.environ.get('SSKY_TEST_UNTIL', '2023-12-31T23:59:59Z')
            result = search(query, since=since, until=until)
            
            assert isinstance(result, PostDataList), "Search should return PostDataList"
    
    def test_07_search_error_scenarios(self):
        """Test error handling scenarios"""
        # Test: No session available
        from ssky.result import SessionError
        with patch('ssky.search.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = None
            
            with pytest.raises(SessionError):
                search("test")
        
        # Test: Empty query
        from ssky.result import AtProtocolSskyError
        with pytest.raises(AtProtocolSskyError):
            search("")
    
    def test_08_search_with_json_format(self, mock_search_environment):
        """Test search with JSON format output"""
        mock_session, mock_client, mock_profile = mock_search_environment
        
        with patch('ssky.search.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            query = os.environ.get('SSKY_TEST_Q', 'test')
            result = search(query, format='json')
            
            assert isinstance(result, PostDataList), "Search should return PostDataList with JSON format"