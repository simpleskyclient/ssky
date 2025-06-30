import os
import shutil
import tempfile
from time import sleep
from dotenv import load_dotenv
from unittest.mock import Mock, patch

from ssky.ssky_session import SskySession

def setup(envs_to_delete=[], no_session_file=False, interval=0):
    if interval > 0:
        sleep(interval)
    load_dotenv('tests/.env')
    for name in envs_to_delete:
        del os.environ[name]
    if no_session_file:
        if os.path.exists(os.path.expanduser('~/.ssky')):
            os.remove(os.path.expanduser('~/.ssky'))



# New utilities for session management optimization

def create_master_session_backup(backup_path):
    """Create a backup of the current session file for testing"""
    session_path = os.path.expanduser('~/.ssky')
    if os.path.exists(session_path):
        shutil.copy2(session_path, backup_path)
        return True
    return False

def restore_session_from_backup(backup_path):
    """Restore session file from backup"""
    session_path = os.path.expanduser('~/.ssky')
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, session_path)
        return True
    return False

def setup_with_session_copy(master_session_path, envs_to_delete=[]):
    """Setup test environment with copied session file"""
    load_dotenv('tests/.env')
    for name in envs_to_delete:
        if name in os.environ:
            del os.environ[name]
    
    # Copy master session to active location
    if master_session_path and os.path.exists(master_session_path):
        session_path = os.path.expanduser('~/.ssky')
        shutil.copy2(master_session_path, session_path)



def has_credentials():
    """Check if SSKY_USER credentials are available"""
    load_dotenv('tests/.env')
    return bool(os.environ.get('SSKY_USER'))

def create_mock_atproto_client():
    """Create mock atproto client for testing without API calls"""
    mock_client = Mock()
    mock_profile = Mock()
    mock_profile.did = "did:plc:test123456789"
    
    # Mock successful login
    mock_client.login.return_value = mock_profile
    mock_client.export_session_string.return_value = '{"test": "session_data"}'
    
    # Mock feed responses with iterable feed lists
    mock_feed_post = Mock()
    mock_feed_post.post = Mock()
    mock_feed_post.post.uri = "at://test.user/app.bsky.feed.post/test123"
    mock_feed_post.post.cid = "testcid123"
    
    # Timeline response
    mock_timeline_response = Mock()
    mock_timeline_response.feed = [mock_feed_post]
    mock_client.get_timeline.return_value = mock_timeline_response
    
    # Author feed response
    mock_author_feed_response = Mock()
    mock_author_feed_response.feed = [mock_feed_post]
    mock_client.get_author_feed.return_value = mock_author_feed_response
    
    # Posts response - default post without viewer info
    mock_post = Mock()
    mock_post.uri = "at://test.user/app.bsky.feed.post/test123"
    mock_post.cid = "testcid123"
    mock_post.viewer = Mock()
    mock_post.viewer.repost = None  # Default: not reposted
    mock_posts_response = Mock()
    mock_posts_response.posts = [mock_post]
    
    # Mock follows response for unfollow functionality
    mock_follow = Mock()
    mock_follow.did = "did:plc:test123"
    mock_follow.handle = "test.bsky.social"
    mock_follow.viewer = Mock()
    mock_follow.viewer.following = "at://test.user/app.bsky.graph.follow/test123"
    
    mock_follows_response = Mock()
    mock_follows_response.follows = [mock_follow]
    mock_client.get_follows.return_value = mock_follows_response
    
    # Mock profile response for follow functionality
    mock_profile_response = Mock()
    mock_profile_response.did = "did:plc:test123"
    mock_client.get_profile.return_value = mock_profile_response
    
    # Mock send_post response with string URI - use a simple object instead of Mock
    class MockSendPostResponse:
        def __init__(self):
            self.uri = "at://test.user/app.bsky.feed.post/test123"
            self.cid = "testcid123"
    
    mock_send_post_response = MockSendPostResponse()
    mock_client.send_post.return_value = mock_send_post_response
    mock_client.send_images.return_value = mock_send_post_response
    
    # Mock repost with viewer info
    mock_repost_post = Mock()
    mock_repost_post.uri = "at://test.user/app.bsky.feed.post/test123"
    mock_repost_post.cid = "testcid123"
    mock_repost_post.viewer = Mock()
    mock_repost_post.viewer.repost = "at://test.user/app.bsky.feed.repost/test123"
    
    mock_repost_posts_response = Mock()
    mock_repost_posts_response.posts = [mock_repost_post]
    
    # For repost/unrepost, we need to return different responses
    # Default to the basic version (not reposted), tests can override as needed
    mock_client.get_posts.return_value = mock_posts_response
    
    # Mock search functionality
    mock_author = Mock()
    mock_author.did = "did:plc:search123"
    mock_author.handle = "search.bsky.social"
    mock_author.display_name = "Search User"
    mock_author.avatar = "https://example.com/avatar.jpg"
    
    mock_record = Mock()
    mock_record.text = "Search result post"
    mock_record.created_at = "2023-01-01T00:00:00.000Z"
    mock_record.facets = None
    
    mock_search_post = Mock()
    mock_search_post.uri = "at://test.user/app.bsky.feed.post/search123"
    mock_search_post.cid = "searchcid123"
    mock_search_post.author = mock_author
    mock_search_post.record = mock_record
    mock_search_post.indexed_at = "2023-01-01T01:00:00.000Z"
    mock_search_post.reply_count = 0
    mock_search_post.repost_count = 0
    mock_search_post.like_count = 0
    mock_search_post.viewer = None
    
    # Ensure URI and CID can be used in string operations
    mock_search_post.__str__ = lambda: "at://test.user/app.bsky.feed.post/search123"
    
    mock_search_response = Mock()
    mock_search_response.posts = [mock_search_post]
    mock_client.app.bsky.feed.search_posts.return_value = mock_search_response
    
    return mock_client, mock_profile

def create_mock_ssky_session():
    """Create mock SskySession for testing without API calls or session files"""
    from unittest.mock import Mock
    
    # Mock profile
    mock_profile = Mock()
    mock_profile.did = "did:plc:test123456789"
    mock_profile.handle = "test.bsky.social"
    mock_profile.display_name = "Test User"
    
    # Mock client
    mock_client = Mock()
    mock_client.get_profile.return_value = mock_profile
    mock_client.get_timeline.return_value = Mock()
    mock_client.get_author_feed.return_value = Mock()
    mock_client.get_posts.return_value = Mock()
    
    # Mock session methods
    mock_session = Mock()
    mock_session.client.return_value = mock_client
    mock_session.profile.return_value = mock_profile
    mock_session.persist.return_value = None
    
    return mock_session, mock_client, mock_profile

class MasterSessionManager:
    """Manages master session backup for all test classes"""
    
    _backup_path = os.path.expanduser('~/.ssky_test_master_session_backup')
    
    @classmethod
    def get_backup_path(cls):
        """Get the master session backup file path"""
        return cls._backup_path
    
    @classmethod
    def exists(cls):
        """Check if master session backup exists"""
        return os.path.exists(cls._backup_path)
    
    @classmethod
    def create_from_current_session(cls):
        """Create master session backup from current session file"""
        session_path = os.path.expanduser('~/.ssky')
        if os.path.exists(session_path):
            return create_master_session_backup(cls._backup_path)
        return False
    
    @classmethod
    def ensure_exists(cls):
        """Ensure master session backup exists, create if needed"""
        if not cls.exists():
            return cls.create_from_current_session()
        return True
    
    @classmethod
    def ensure_session_available(cls):
        """Ensure session file is available - restore from backup if needed"""
        session_path = os.path.expanduser('~/.ssky')
        
        # If session file doesn't exist but backup exists, restore it
        if not os.path.exists(session_path) and cls.exists():
            return cls.restore_to_session()
        
        # If session file exists, ensure backup exists
        if os.path.exists(session_path):
            if not cls.exists():
                return cls.create_from_current_session()
            return True
        
        return False
    
    @classmethod
    def restore_to_session(cls):
        """Restore master session backup to current session file"""
        if cls.exists():
            session_path = os.path.expanduser('~/.ssky')
            shutil.copy2(cls._backup_path, session_path)
            return True
        return False
    
    @classmethod
    def cleanup(cls):
        """Remove master session backup file"""
        if cls.exists():
            os.remove(cls._backup_path)
            return True
        return False

class BaseSequentialTest:
    """Base class for sequential tests to minimize Bluesky API calls
    
    Provides common setup methods for session backup management.
    All test classes should inherit from this to avoid code duplication.
    """
    
    @property
    def master_session_backup(self):
        """Get master session backup path"""
        return MasterSessionManager.get_backup_path()
    
    @classmethod
    def setup_class(cls):
        """Class setup - ensure session file and backup are available"""
        # Load environment variables first for all tests in this class
        load_dotenv('tests/.env')
        MasterSessionManager.ensure_session_available()
    
