import os
import tempfile
import pytest
from unittest.mock import patch, Mock, MagicMock
from time import sleep

from ssky.delete import delete
from ssky.post import post, get_tags, get_links, get_mentions
from ssky.post_data_list import PostDataList
from ssky.util import join_uri_cid
from ssky.result import ErrorResult, DryRunResult
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
        
        # Dry run should return a DryRunResult object
        assert isinstance(dry_result, DryRunResult), "Dry run should return DryRunResult"
        assert dry_result.message == message, "DryRunResult should contain the message"
    
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
        from ssky.result import SessionError
        with patch('ssky.post.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = None
            
            with pytest.raises(SessionError):
                post(message="test")
        
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
        from ssky.result import SskyError
        with pytest.raises(SskyError):
            delete("invalid://uri")

    def test_05_post_facets_dry_run_hashtags(self):
        """Test dry run with hashtags extracts tags properly"""
        message = "Testing #hashtag extraction in #dryrun mode"
        
        dry_result = post(message=message, dry=True)
        
        assert isinstance(dry_result, DryRunResult)
        assert dry_result.message == message
        assert len(dry_result.tags) == 2
        assert '#hashtag' in dry_result.tags
        assert '#dryrun' in dry_result.tags
        assert len(dry_result.links) == 0
        assert len(dry_result.mentions) == 0

    def test_06_post_facets_dry_run_urls(self):
        """Test dry run with URLs extracts links and cards properly"""
        message = "Check out https://www.example.com/ for more info"
        
        # Mock get_card to avoid actual HTTP requests
        with patch('ssky.post.get_card') as mock_get_card:
            mock_get_card.return_value = [{
                'title': 'Example Domain',
                'description': 'This domain is for use in examples',
                'thumbnail': None,
                'uri': 'https://www.example.com/'
            }]
            
            dry_result = post(message=message, dry=True)
            
            assert isinstance(dry_result, DryRunResult)
            assert dry_result.message == message
            assert len(dry_result.links) == 1
            assert 'https://www.example.com/' in dry_result.links
            assert dry_result.card is not None
            assert dry_result.card['title'] == 'Example Domain'
            assert len(dry_result.tags) == 0
            assert len(dry_result.mentions) == 0

    def test_07_post_facets_dry_run_mentions(self):
        """Test dry run with mentions extracts mentions properly"""
        # Mock the IdResolver to avoid actual network calls
        with patch('ssky.post.IdResolver') as mock_resolver_class:
            mock_resolver = MagicMock()
            mock_handle_resolver = MagicMock()
            mock_handle_resolver.resolve.return_value = "did:plc:test123"
            mock_resolver.handle = mock_handle_resolver
            mock_resolver_class.return_value = mock_resolver
            
            message = "Hello @test.bsky.social, how are you?"
            
            dry_result = post(message=message, dry=True)
            
            assert isinstance(dry_result, DryRunResult)
            assert dry_result.message == message
            assert len(dry_result.mentions) == 1
            assert '@test.bsky.social' in dry_result.mentions
            assert len(dry_result.tags) == 0
            assert len(dry_result.links) == 0

    def test_08_post_facets_dry_run_all_together(self):
        """Test dry run with URLs, hashtags, and mentions all together"""
        # Mock dependencies
        with patch('ssky.post.IdResolver') as mock_resolver_class:
            mock_resolver = MagicMock()
            mock_handle_resolver = MagicMock()
            mock_handle_resolver.resolve.return_value = "did:plc:test123"
            mock_resolver.handle = mock_handle_resolver
            mock_resolver_class.return_value = mock_resolver
            
            with patch('ssky.post.get_card') as mock_get_card:
                mock_get_card.return_value = [{
                    'title': 'Example Domain',
                    'description': 'This domain is for use in examples',
                    'thumbnail': None,
                    'uri': 'https://www.example.com/'
                }]
                
                message = "Check out https://www.example.com/ #awesome @test.bsky.social! #bluesky"
                
                dry_result = post(message=message, dry=True)
                
                assert isinstance(dry_result, DryRunResult)
                assert dry_result.message == message
                
                # Check all facets were extracted
                assert len(dry_result.links) == 1
                assert 'https://www.example.com/' in dry_result.links
                assert len(dry_result.tags) == 2
                assert '#awesome' in dry_result.tags
                assert '#bluesky' in dry_result.tags
                assert len(dry_result.mentions) == 1
                assert '@test.bsky.social' in dry_result.mentions
                assert dry_result.card is not None

    def test_09_post_facets_processing_with_mock(self):
        """Test actual post with facets processing using mocked client"""
        if not has_credentials():
            pytest.skip("No credentials available")
        
        # Create mock environment
        mock_session, mock_client, mock_profile = create_mock_ssky_session()
        
        # Mock dependencies
        with patch('ssky.post.IdResolver') as mock_resolver_class:
            mock_resolver = MagicMock()
            mock_handle_resolver = MagicMock()
            mock_handle_resolver.resolve.return_value = "did:plc:test123"
            mock_resolver.handle = mock_handle_resolver
            mock_resolver_class.return_value = mock_resolver
            
            with patch('ssky.post.get_card') as mock_get_card:
                mock_get_card.return_value = [{
                    'title': 'Example Domain',
                    'description': 'This domain is for use in examples',
                    'thumbnail': None,
                    'uri': 'https://www.example.com/'
                }]
                
                # Mock the retrieved post for verification
                mock_retrieved_post = Mock()
                mock_retrieved_post.uri = "at://test.user/app.bsky.feed.post/test123"
                mock_retrieved_post.cid = "testcid123"
                mock_retrieved_post.author = Mock()
                mock_retrieved_post.author.did = "did:plc:test123"
                mock_retrieved_post.author.handle = "test.bsky.social"
                mock_retrieved_post.record = Mock()
                mock_retrieved_post.record.text = "Test message with #hashtag https://www.example.com/ @test.bsky.social"
                
                mock_get_posts_response = Mock()
                mock_get_posts_response.posts = [mock_retrieved_post]
                mock_client.get_posts.return_value = mock_get_posts_response
                
                with patch('ssky.post.ssky_client') as mock_ssky_client:
                    mock_ssky_client.return_value = mock_client
                    
                    message = "Test message with #hashtag https://www.example.com/ @test.bsky.social"
                    result = post(message=message, dry=False)
                    
                    assert isinstance(result, PostDataList)
                    
                    # Verify that send_post was called with facets
                    mock_client.send_post.assert_called_once()
                    call_args = mock_client.send_post.call_args
                    
                    # Check that facets were passed
                    assert 'facets' in call_args.kwargs
                    facets = call_args.kwargs['facets']
                    assert len(facets) >= 3  # At least hashtag, link, and mention

    def test_10_get_tags_function(self):
        """Test the get_tags helper function"""
        # Test message with hashtags
        message = "This is a #test message with #multiple #hashtags"
        tags = get_tags(message)
        
        assert len(tags) == 3
        tag_names = [item['name'] for item in tags.values()]
        assert '#test' in tag_names
        assert '#multiple' in tag_names
        assert '#hashtags' in tag_names
        
        # Test message without hashtags
        message_no_tags = "This message has no hashtags"
        tags_empty = get_tags(message_no_tags)
        assert len(tags_empty) == 0

    def test_11_get_links_function(self):
        """Test the get_links helper function"""
        # Test message with URLs
        message = "Check out https://example.com and http://test.org"
        links = get_links(message)
        
        assert len(links) == 2
        link_uris = [item['uri'] for item in links.values()]
        assert 'https://example.com' in link_uris
        assert 'http://test.org' in link_uris
        
        # Test message without URLs
        message_no_links = "This message has no links"
        links_empty = get_links(message_no_links)
        assert len(links_empty) == 0

    def test_12_get_mentions_function(self):
        """Test the get_mentions helper function"""
        # Mock the IdResolver to avoid actual network calls
        with patch('ssky.post.IdResolver') as mock_resolver_class:
            mock_resolver = MagicMock()
            mock_handle_resolver = MagicMock()
            mock_handle_resolver.resolve.return_value = "did:plc:test123"
            mock_resolver.handle = mock_handle_resolver
            mock_resolver_class.return_value = mock_resolver
            
            # Test message with mentions
            message = "Hello @user.bsky.social and @test.bsky.social"
            mentions = get_mentions(message)
            
            assert len(mentions) == 2
            mention_handles = [item['handle'] for item in mentions.values()]
            assert '@user.bsky.social' in mention_handles
            assert '@test.bsky.social' in mention_handles
            
            # Verify DIDs were resolved
            mention_dids = [item['did'] for item in mentions.values()]
            assert all(did == "did:plc:test123" for did in mention_dids)
        
        # Test message without mentions
        message_no_mentions = "This message has no mentions"
        mentions_empty = get_mentions(message_no_mentions)
        assert len(mentions_empty) == 0

