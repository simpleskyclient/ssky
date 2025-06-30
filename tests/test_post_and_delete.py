import os
import tempfile
import pytest
from unittest.mock import patch, Mock
from time import sleep

from ssky.delete import delete
from ssky.post import post
from ssky.post_data_list import PostDataList
from ssky.util import join_uri_cid, ErrorResult
from ssky.ssky_session import SskySession
from tests.common import create_mock_ssky_session, has_credentials

@pytest.fixture
def mock_post_environment():
    """Setup test environment for post/delete tests"""
    if not has_credentials():
        pytest.skip("No credentials available")
    
    # Create mock session for all post/delete tests
    mock_session, mock_client, mock_profile = create_mock_ssky_session()
    
    # Set up proper mock responses for post/delete functionality
    # Mock post creation response
    mock_post_response = Mock()
    mock_post_response.uri = "at://test.user/app.bsky.feed.post/test123"
    mock_post_response.cid = "testcid123"
    mock_client.send_post.return_value = mock_post_response
    
    # Mock send_images response (for when images are involved)
    mock_images_response = Mock()
    mock_images_response.uri = "at://test.user/app.bsky.feed.post/test123"
    mock_images_response.cid = "testcid123"
    mock_client.send_images.return_value = mock_images_response
    
    # Mock get_posts response (for post retrieval after creation)
    mock_retrieved_post = Mock()
    mock_retrieved_post.uri = "at://test.user/app.bsky.feed.post/test123"
    mock_retrieved_post.cid = "testcid123"
    mock_retrieved_post.author = Mock()
    mock_retrieved_post.author.did = "did:plc:test123"
    mock_retrieved_post.author.handle = "test.bsky.social"
    mock_retrieved_post.record = Mock()
    mock_retrieved_post.record.text = "Test post message"
    
    mock_get_posts_response = Mock()
    mock_get_posts_response.posts = [mock_retrieved_post]
    mock_client.get_posts.return_value = mock_get_posts_response
    
    # Mock delete response
    mock_client.delete_post.return_value = True
    
    return mock_session, mock_client, mock_profile

class TestPostDeleteSequential:
    """Sequential post and delete tests using mocked SskySession
    
    Strategy: 1 real post/delete cycle + mocked tests for other scenarios
    This reduces API calls and avoids rate limits.
    """
    
    def test_01_post_dry_run(self):
        """Test dry run functionality without API calls"""
        # Test dry run - should not make API calls
        message = os.environ.get('SSKY_TEST_POST_TEXT', 'Test post message')
        image = os.environ.get('SSKY_TEST_POST_IMAGE')
        
        dry_result = post(message=message, image=[image] if image else [], dry=True)
        
        # Dry run should return a list (preview)
        assert isinstance(dry_result, list), "Dry run should return list"
    
    def test_02_real_post_quote_reply_delete_cycle(self):
        """Real API test - post, quote, reply, and delete cycle (only real API test in this file)"""
        # Skip if no credentials available
        if not has_credentials():
            pytest.skip("SSKY_USER environment variable not set")
        
        # Skip if SSKY_SKIP_REAL_API_TESTS is set
        if os.environ.get('SSKY_SKIP_REAL_API_TESTS'):
            pytest.skip("Real API tests disabled by SSKY_SKIP_REAL_API_TESTS")
        
        # This test uses real API calls - no mocking
        created_posts = []  # Track created posts for cleanup
        
        try:
            # Post with test marker
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            message = f"[TEST {timestamp}] {os.environ.get('SSKY_TEST_POST_TEXT', 'Test post message')}"
            image = os.environ.get('SSKY_TEST_POST_IMAGE')
            
            post_result = post(message=message, image=[image] if image else None)
            
            # Check if post failed due to rate limiting or other errors
            if isinstance(post_result, ErrorResult):
                if post_result.http_code == 429:
                    pytest.skip("Rate limit exceeded - skipping test")
                else:
                    assert False, f"Post failed: {post_result.message}"
            
            assert isinstance(post_result, PostDataList), "Post should return PostDataList"
            created_posts.append(post_result[0].uri)
            
            source_uri_cid = join_uri_cid(post_result[0].uri, post_result[0].cid)
            sleep(5)
            
            # Quote with test marker
            quote_text = f"[TEST {timestamp}] {os.environ.get('SSKY_TEST_POST_QUOTE_TEXT', 'Quote test')}"
            quote_result = post(message=quote_text, quote=source_uri_cid)
            if isinstance(quote_result, ErrorResult):
                if quote_result.http_code == 429:
                    pytest.skip("Rate limit exceeded - skipping test")
                else:
                    assert False, f"Quote failed: {quote_result.message}"
            
            assert isinstance(quote_result, PostDataList), "Quote should return PostDataList"
            created_posts.append(quote_result[0].uri)
            
            sleep(5)
            
            # Reply with test marker
            reply_text = f"[TEST {timestamp}] {os.environ.get('SSKY_TEST_POST_REPLY_TEXT', 'Reply test')}"
            reply_result = post(message=reply_text, reply_to=source_uri_cid)
            if isinstance(reply_result, ErrorResult):
                if reply_result.http_code == 429:
                    pytest.skip("Rate limit exceeded - skipping test")
                else:
                    assert False, f"Reply failed: {reply_result.message}"
            
            assert isinstance(reply_result, PostDataList), "Reply should return PostDataList"
            created_posts.append(reply_result[0].uri)
            
            sleep(5)
            
            # Delete in reverse order (reply -> quote -> original)
            for uri in reversed(created_posts):
                delete_result = delete(uri)
                if isinstance(delete_result, str):
                    print(f"Successfully deleted: {uri}")
                else:
                    print(f"Failed to delete: {uri}")
            
        except Exception as e:
            # Emergency cleanup: try to delete any created posts
            print(f"Test failed with error: {e}")
            print("Attempting emergency cleanup of created posts...")
            for uri in reversed(created_posts):
                try:
                    delete_result = delete(uri)
                    print(f"Emergency cleanup - deleted: {uri}")
                except Exception as cleanup_error:
                    print(f"Emergency cleanup failed for {uri}: {cleanup_error}")
            raise  # Re-raise the original exception
        
        finally:
            SskySession.clear()
    
    def test_03_post_with_json_format(self, mock_post_environment):
        """Test post with JSON format output"""
        mock_session, mock_client, mock_profile = mock_post_environment
        
        with patch('ssky.post.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client
            
            # Test with JSON format
            message = "Test post message"
            result = post(message=message, format='json')
            
            # Should return PostDataList
            assert isinstance(result, PostDataList), "Should return PostDataList"
    
    def test_04_post_error_scenarios(self):
        """Test error handling scenarios"""
        # Test 1: No session available
        with patch('ssky.post.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = None
            
            result = post(message="test")
            assert isinstance(result, ErrorResult), "Post should return ErrorResult when no session available"
            assert result.http_code == 401, "Should return 401 error code"
        
        # Test 2: Empty message with mocked stdin and mocked client
        import io
        with patch('sys.stdin', io.StringIO("")):
            with patch('ssky.post.ssky_client') as mock_ssky_client:
                mock_session, mock_client, mock_profile = create_mock_ssky_session()
                
                # Set up proper string URIs for the mock responses
                mock_client.send_post.return_value.uri = "at://test.user/app.bsky.feed.post/empty123"
                mock_client.send_post.return_value.cid = "emptycid123"
                mock_client.send_images.return_value.uri = "at://test.user/app.bsky.feed.post/empty123"
                mock_client.send_images.return_value.cid = "emptycid123"
                
                # Mock get_posts response with proper string URIs
                mock_retrieved_post = Mock()
                mock_retrieved_post.uri = "at://test.user/app.bsky.feed.post/empty123"
                mock_retrieved_post.cid = "emptycid123"
                mock_retrieved_post.author = Mock()
                mock_retrieved_post.author.did = "did:plc:test123"
                mock_retrieved_post.author.handle = "test.bsky.social"
                mock_retrieved_post.record = Mock()
                mock_retrieved_post.record.text = ""
                
                mock_get_posts_response = Mock()
                mock_get_posts_response.posts = [mock_retrieved_post]
                mock_client.get_posts.return_value = mock_get_posts_response
                
                mock_ssky_client.return_value = mock_client
                
                result = post(message="")
                # Empty message creates a valid post when mocked
                assert isinstance(result, PostDataList), "Post should return PostDataList even with empty message"
        
        # Test 3: Test delete with invalid URI
        result = delete("invalid://uri")
        assert isinstance(result, ErrorResult), "Delete should return ErrorResult with invalid URI"