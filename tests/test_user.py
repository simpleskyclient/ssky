import os
import tempfile
import pytest
from unittest.mock import patch, Mock

from ssky.profile_list import ProfileList
from ssky.user import user
from ssky.ssky_session import SskySession
from ssky.util import ErrorResult
from tests.common import create_mock_ssky_session, has_credentials

@pytest.fixture
def mock_user_environment():
    """Setup test environment for user tests"""
    if not has_credentials():
        pytest.skip("No credentials available")
    
    # Create mock session for all user tests
    mock_session, mock_client, mock_profile = create_mock_ssky_session()
    
    # Set up proper mock responses for user search functionality
    # Mock user/actor for search response
    mock_actor = Mock()
    mock_actor.did = "did:plc:test123"
    mock_actor.handle = "test.bsky.social"
    mock_actor.display_name = "Test User"
    mock_actor.avatar = "https://example.com/avatar.jpg"
    
    # Set up user search response
    mock_search_response = Mock()
    mock_search_response.actors = [mock_actor]
    mock_client.app.bsky.actor.search_actors.return_value = mock_search_response
    
    return mock_session, mock_client, mock_profile

class TestUserSequential:
    """Sequential user search tests using mocked SskySession
    
    Strategy: 1 real user search + mocked tests for other scenarios
    This reduces API calls and avoids rate limits.
    """
    
    def test_01_real_user_search(self):
        """Real API test - basic user search functionality (only real API test in this file)"""
        # Skip if no credentials available
        if not has_credentials():
            pytest.skip("SSKY_USER environment variable not set")
        
        # This test uses real API calls - no mocking
        try:
            query = os.environ.get('SSKY_TEST_Q', 'test')
            result = user(query)
            assert isinstance(result, ProfileList), "User search should return ProfileList"
        finally:
            SskySession.clear()
    
    def test_02_user_search_with_limit(self, mock_user_environment):
        """Test user search with limit using mocked session"""
        mock_session, mock_client, mock_profile = mock_user_environment
        
        # Mock user search response with limited results
        limit = int(os.environ.get('SSKY_TEST_LIMIT', '3'))
        mock_actors = []
        for i in range(limit):
            mock_actor = Mock()
            mock_actor.did = f"did:plc:test{i}"
            mock_actor.handle = f"test{i}.bsky.social"
            mock_actors.append(mock_actor)
        
        mock_search_response = Mock()
        mock_search_response.actors = mock_actors
        mock_client.app.bsky.actor.search_actors.return_value = mock_search_response
        
        with patch('ssky.user.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            query = os.environ.get('SSKY_TEST_Q', 'test')
            result = user(query, limit=limit)
            
            assert isinstance(result, ProfileList), "User search should return ProfileList"
            assert len(result) == limit, f"Should return exactly {limit} results"
    
    def test_03_user_search_with_no_results(self, mock_user_environment):
        """Test user search with query that returns no results"""
        mock_session, mock_client, mock_profile = mock_user_environment
        
        # Mock user search response with no results
        mock_search_response = Mock()
        mock_search_response.actors = []
        mock_client.app.bsky.actor.search_actors.return_value = mock_search_response
        
        with patch('ssky.user.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            query = os.environ.get('SSKY_TEST_Q_WITH_NO_RESULTS', 'nonexistentuserthatreturnsnothing123')
            result = user(query)
            
            assert isinstance(result, ProfileList), "User search should return ProfileList even with no results"
            assert len(result) == 0, "Should return empty results"
    
    def test_04_user_search_error_scenarios(self):
        """Test error handling scenarios"""
        # Test 1: No session available
        with patch('ssky.user.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = None
            
            result = user("test query")
            assert isinstance(result, ErrorResult), "User search should return ErrorResult when no session available"
            assert result.http_code == 401, "Should return 401 error code"
        
        # Test 2: Empty query
        result = user("")
        assert isinstance(result, ErrorResult), "User search should return ErrorResult with empty query"
    
    def test_05_user_search_with_json_format(self, mock_user_environment):
        """Test user search with JSON format output"""
        mock_session, mock_client, mock_profile = mock_user_environment
        
        with patch('ssky.user.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            query = os.environ.get('SSKY_TEST_Q', 'test')
            result = user(query, format='json')
            
            assert isinstance(result, ProfileList), "User search should return ProfileList with JSON format"