import os
import pytest
from unittest.mock import Mock, patch
from atproto import models

from ssky.get import get
from ssky.thread_data import ThreadData
from ssky.thread_data_list import ThreadDataList
from ssky.ssky_session import SskySession
from tests.common import create_mock_ssky_session, has_credentials


@pytest.fixture
def mock_thread_environment():
    """Setup test environment for thread tests"""
    if not has_credentials():
        pytest.skip("No credentials available")

    # Create mock session for all thread tests
    mock_session, mock_client, mock_profile = create_mock_ssky_session()

    # Mock post for posts response
    mock_post = Mock()
    mock_post.uri = "at://test.user/app.bsky.feed.post/test123"
    mock_post.cid = "testcid123"
    mock_post.author = Mock()
    mock_post.author.did = "did:plc:test123"
    mock_post.author.handle = "test.bsky.social"
    mock_post.record = Mock()
    mock_post.record.text = "Root post content"

    # Mock reply post
    mock_reply = Mock()
    mock_reply.uri = "at://test.user/app.bsky.feed.post/reply123"
    mock_reply.cid = "replycid123"
    mock_reply.author = Mock()
    mock_reply.author.did = "did:plc:test123"
    mock_reply.author.handle = "test.bsky.social"
    mock_reply.record = Mock()
    mock_reply.record.text = "Reply content"

    # Mock feed post for feed responses
    mock_feed_post = Mock()
    mock_feed_post.post = mock_post

    # Set up timeline response with single post
    mock_timeline_response = Mock()
    mock_timeline_response.feed = [mock_feed_post]
    mock_client.get_timeline.return_value = mock_timeline_response

    # Set up thread response
    mock_reply_node = Mock(spec=models.AppBskyFeedDefs.ThreadViewPost)
    mock_reply_node.post = mock_reply
    mock_reply_node.replies = None

    mock_thread_node = Mock(spec=models.AppBskyFeedDefs.ThreadViewPost)
    mock_thread_node.post = mock_post
    mock_thread_node.replies = [mock_reply_node]

    mock_thread_response = Mock(spec=models.AppBskyFeedGetPostThread.Response)
    mock_thread_response.thread = mock_thread_node

    mock_client.get_post_thread.return_value = mock_thread_response

    return mock_session, mock_client, mock_profile, mock_post, mock_reply


class TestThreadDataSequential:
    """Sequential tests for ThreadData class"""

    def test_01_thread_data_initialization(self, mock_thread_environment):
        """Test ThreadData initialization with thread response"""
        mock_session, mock_client, mock_profile, mock_post, mock_reply = mock_thread_environment

        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client

            # Get thread response
            thread_response = mock_client.get_post_thread("at://test.user/app.bsky.feed.post/test123")

            # Create ThreadData
            thread_data = ThreadData(thread_response)

            assert len(thread_data.posts) == 2, "Thread should have 2 posts (root + reply)"
            assert thread_data.posts[0][0].uri == "at://test.user/app.bsky.feed.post/test123"
            assert thread_data.posts[0][1] == 0, "Root post should have depth 0"
            assert thread_data.posts[1][0].uri == "at://test.user/app.bsky.feed.post/reply123"
            assert thread_data.posts[1][1] == 1, "Reply should have depth 1"


class TestThreadDataListSequential:
    """Sequential tests for ThreadDataList class"""

    def test_01_thread_data_list_initialization(self):
        """Test ThreadDataList initialization"""
        thread_list = ThreadDataList()
        assert len(thread_list.threads) == 0, "New ThreadDataList should be empty"

    def test_02_thread_data_list_append(self, mock_thread_environment):
        """Test appending ThreadData to ThreadDataList"""
        mock_session, mock_client, mock_profile, mock_post, mock_reply = mock_thread_environment

        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client

            # Create ThreadData
            thread_response = mock_client.get_post_thread("at://test.user/app.bsky.feed.post/test123")
            thread_data = ThreadData(thread_response)

            # Create ThreadDataList and append
            thread_list = ThreadDataList()
            thread_list.append(thread_data)

            assert len(thread_list.threads) == 1, "ThreadDataList should have 1 thread after append"


class TestGetWithThreadSequential:
    """Sequential tests for get() with --thread option"""

    def test_01_get_timeline_with_thread(self, mock_thread_environment):
        """Test get timeline with --thread option"""
        mock_session, mock_client, mock_profile, mock_post, mock_reply = mock_thread_environment

        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client

            result = get(target=None, thread=True)

            assert isinstance(result, ThreadDataList), "Get timeline with --thread should return ThreadDataList"
            assert len(result.threads) == 1, "Should have 1 thread for the timeline post"
            assert mock_client.get_post_thread.called, "get_post_thread should be called"

    def test_02_get_timeline_with_thread_json_format(self, mock_thread_environment):
        """Test get timeline with --thread and JSON format (should ignore --thread)"""
        mock_session, mock_client, mock_profile, mock_post, mock_reply = mock_thread_environment

        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client

            from ssky.post_data_list import PostDataList
            result = get(target=None, thread=True, format='json')

            assert isinstance(result, PostDataList), "Get with --thread and JSON format should return PostDataList"
            assert not mock_client.get_post_thread.called, "get_post_thread should NOT be called for JSON format"

    def test_03_get_timeline_with_thread_simple_json_format(self, mock_thread_environment):
        """Test get timeline with --thread and simple_json format (should ignore --thread)"""
        mock_session, mock_client, mock_profile, mock_post, mock_reply = mock_thread_environment

        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client

            from ssky.post_data_list import PostDataList
            result = get(target=None, thread=True, format='simple_json')

            assert isinstance(result, PostDataList), "Get with --thread and simple_json format should return PostDataList"
            # Reset mock before checking
            mock_client.get_post_thread.reset_mock()

    def test_04_get_author_feed_with_thread(self, mock_thread_environment):
        """Test get author feed with --thread option"""
        mock_session, mock_client, mock_profile, mock_post, mock_reply = mock_thread_environment

        # Set up author feed response
        mock_feed_post = Mock()
        mock_feed_post.post = mock_post
        mock_author_feed_response = Mock()
        mock_author_feed_response.feed = [mock_feed_post]
        mock_client.get_author_feed.return_value = mock_author_feed_response

        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client

            result = get(target='test.bsky.social', thread=True)

            assert isinstance(result, ThreadDataList), "Get author feed with --thread should return ThreadDataList"
            assert len(result.threads) == 1, "Should have 1 thread for the author feed post"
            assert mock_client.get_post_thread.called, "get_post_thread should be called"

    def test_05_get_single_post_with_thread(self, mock_thread_environment):
        """Test get single post with --thread option"""
        mock_session, mock_client, mock_profile, mock_post, mock_reply = mock_thread_environment

        # Set up posts response
        mock_posts_response = Mock()
        mock_posts_response.posts = [mock_post]
        mock_client.get_posts.return_value = mock_posts_response

        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client

            result = get(target='at://test.user/app.bsky.feed.post/test123', thread=True)

            assert isinstance(result, ThreadDataList), "Get single post with --thread should return ThreadDataList"
            assert len(result.threads) == 1, "Should have 1 thread for the post"
            assert mock_client.get_post_thread.called, "get_post_thread should be called"

    def test_06_get_with_thread_depth_and_parent_height(self, mock_thread_environment):
        """Test get with custom thread_depth and thread_parent_height"""
        mock_session, mock_client, mock_profile, mock_post, mock_reply = mock_thread_environment

        with patch('ssky.get.ssky_client') as mock_ssky_client:
            mock_ssky_client.return_value = mock_client

            result = get(target=None, thread=True, thread_depth=5, thread_parent_height=2)

            assert isinstance(result, ThreadDataList), "Get with thread params should return ThreadDataList"
            assert mock_client.get_post_thread.called, "get_post_thread should be called"

            # Verify get_post_thread was called with correct parameters
            call_args = mock_client.get_post_thread.call_args
            assert call_args[1]['depth'] == 5, "thread_depth should be passed to get_post_thread"
            assert call_args[1]['parent_height'] == 2, "thread_parent_height should be passed to get_post_thread"
