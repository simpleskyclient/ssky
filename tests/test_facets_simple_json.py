import json
import pytest
from unittest.mock import Mock, PropertyMock
from atproto_client import models

from ssky.post_data_list import PostDataList


class MockFeature:
    """Mock feature that only has specific attributes"""
    pass


class MockLinkFeature(MockFeature):
    def __init__(self, uri):
        self.uri = uri


class MockMentionFeature(MockFeature):
    def __init__(self, did):
        self.did = did


class MockTagFeature(MockFeature):
    def __init__(self, tag):
        self.tag = tag


class TestFacetsSimpleJson:
    """Test facets extraction for simple-json output format"""

    def create_mock_post_with_facets(self, text, facets):
        """Helper to create a mock post with specified facets"""
        mock_post = Mock(spec=models.AppBskyFeedDefs.PostView)
        mock_post.uri = "at://did:plc:test/app.bsky.feed.post/test123"
        mock_post.cid = "testcid123"

        # Mock author
        mock_post.author = Mock()
        mock_post.author.did = "did:plc:test123"
        mock_post.author.handle = "test.bsky.social"
        mock_post.author.display_name = "Test User"
        mock_post.author.avatar = "https://example.com/avatar.jpg"

        # Mock record with text and facets
        mock_post.record = Mock()
        mock_post.record.text = text
        mock_post.record.facets = facets
        mock_post.record.created_at = "2024-01-01T00:00:00.000Z"

        # Mock counts
        mock_post.reply_count = 0
        mock_post.repost_count = 0
        mock_post.like_count = 0
        mock_post.indexed_at = "2024-01-01T00:00:00.000Z"

        # Mock viewer
        mock_post.viewer = None

        return mock_post

    def test_extract_facets_with_links(self):
        """Test facets extraction with link facets"""
        text = "Check out https://example.com for more info"

        # Create link facet
        link_facet = Mock()
        link_facet.index = Mock()
        link_facet.index.byte_start = 10
        link_facet.index.byte_end = 29  # Updated: doesn't include space after URL

        link_feature = MockLinkFeature("https://example.com")
        link_facet.features = [link_feature]

        mock_post = self.create_mock_post_with_facets(text, [link_facet])

        # Create PostDataList.Item
        item = PostDataList.Item(mock_post)

        # Extract facets
        facets_data = item._extract_facets_data()

        # Verify
        assert len(facets_data["links"]) == 1
        assert facets_data["links"][0]["url"] == "https://example.com"
        assert facets_data["links"][0]["byte_start"] == 10
        assert facets_data["links"][0]["byte_end"] == 29
        assert facets_data["links"][0]["text"] == "https://example.com"
        assert len(facets_data["mentions"]) == 0
        assert len(facets_data["tags"]) == 0

    def test_extract_facets_with_mentions(self):
        """Test facets extraction with mention facets"""
        text = "Hello @user.bsky.social how are you?"

        # Create mention facet
        mention_facet = Mock()
        mention_facet.index = Mock()
        mention_facet.index.byte_start = 6
        mention_facet.index.byte_end = 23

        mention_feature = MockMentionFeature("did:plc:abc123")
        mention_facet.features = [mention_feature]

        mock_post = self.create_mock_post_with_facets(text, [mention_facet])

        # Create PostDataList.Item
        item = PostDataList.Item(mock_post)

        # Extract facets
        facets_data = item._extract_facets_data()

        # Verify
        assert len(facets_data["mentions"]) == 1
        assert facets_data["mentions"][0]["handle"] == "user.bsky.social"
        assert facets_data["mentions"][0]["did"] == "did:plc:abc123"
        assert facets_data["mentions"][0]["byte_start"] == 6
        assert facets_data["mentions"][0]["byte_end"] == 23
        assert facets_data["mentions"][0]["text"] == "@user.bsky.social"
        assert len(facets_data["links"]) == 0
        assert len(facets_data["tags"]) == 0

    def test_extract_facets_with_tags(self):
        """Test facets extraction with tag facets"""
        text = "This is a test post #bluesky"

        # Create tag facet
        tag_facet = Mock()
        tag_facet.index = Mock()
        tag_facet.index.byte_start = 20
        tag_facet.index.byte_end = 28

        tag_feature = MockTagFeature("bluesky")
        tag_facet.features = [tag_feature]

        mock_post = self.create_mock_post_with_facets(text, [tag_facet])

        # Create PostDataList.Item
        item = PostDataList.Item(mock_post)

        # Extract facets
        facets_data = item._extract_facets_data()

        # Verify
        assert len(facets_data["tags"]) == 1
        assert facets_data["tags"][0]["tag"] == "bluesky"
        assert facets_data["tags"][0]["byte_start"] == 20
        assert facets_data["tags"][0]["byte_end"] == 28
        assert facets_data["tags"][0]["text"] == "#bluesky"
        assert len(facets_data["links"]) == 0
        assert len(facets_data["mentions"]) == 0

    def test_extract_facets_mixed(self):
        """Test facets extraction with all types"""
        text = "Check https://bsky.app @user.bsky.social #atproto"

        # Create link facet
        link_facet = Mock()
        link_facet.index = Mock()
        link_facet.index.byte_start = 6
        link_facet.index.byte_end = 22
        link_feature = MockLinkFeature("https://bsky.app")
        link_facet.features = [link_feature]

        # Create mention facet
        mention_facet = Mock()
        mention_facet.index = Mock()
        mention_facet.index.byte_start = 23
        mention_facet.index.byte_end = 40
        mention_feature = MockMentionFeature("did:plc:xyz789")
        mention_facet.features = [mention_feature]

        # Create tag facet
        tag_facet = Mock()
        tag_facet.index = Mock()
        tag_facet.index.byte_start = 41
        tag_facet.index.byte_end = 49
        tag_feature = MockTagFeature("atproto")
        tag_facet.features = [tag_feature]

        mock_post = self.create_mock_post_with_facets(text, [link_facet, mention_facet, tag_facet])

        # Create PostDataList.Item
        item = PostDataList.Item(mock_post)

        # Extract facets
        facets_data = item._extract_facets_data()

        # Verify all types
        assert len(facets_data["links"]) == 1
        assert facets_data["links"][0]["url"] == "https://bsky.app"

        assert len(facets_data["mentions"]) == 1
        assert facets_data["mentions"][0]["handle"] == "user.bsky.social"
        assert facets_data["mentions"][0]["did"] == "did:plc:xyz789"

        assert len(facets_data["tags"]) == 1
        assert facets_data["tags"][0]["tag"] == "atproto"

    def test_extract_facets_empty(self):
        """Test facets extraction with no facets"""
        text = "Plain text post with no facets"

        mock_post = self.create_mock_post_with_facets(text, None)

        # Create PostDataList.Item
        item = PostDataList.Item(mock_post)

        # Extract facets
        facets_data = item._extract_facets_data()

        # Verify empty arrays
        assert len(facets_data["links"]) == 0
        assert len(facets_data["mentions"]) == 0
        assert len(facets_data["tags"]) == 0

    def test_extract_facets_multibyte(self):
        """Test facets extraction with multibyte characters (emoji)"""
        text = "Hello 👋 check https://example.com"

        # Note: 👋 is 4 bytes in UTF-8
        # "Hello " = 6 bytes
        # "👋" = 4 bytes
        # " check " = 7 bytes
        # Total before URL = 17 bytes

        # Create link facet
        link_facet = Mock()
        link_facet.index = Mock()
        link_facet.index.byte_start = 17
        link_facet.index.byte_end = 37

        link_feature = MockLinkFeature("https://example.com")
        link_facet.features = [link_feature]

        mock_post = self.create_mock_post_with_facets(text, [link_facet])

        # Create PostDataList.Item
        item = PostDataList.Item(mock_post)

        # Extract facets
        facets_data = item._extract_facets_data()

        # Verify
        assert len(facets_data["links"]) == 1
        assert facets_data["links"][0]["url"] == "https://example.com"
        assert facets_data["links"][0]["byte_start"] == 17
        assert facets_data["links"][0]["byte_end"] == 37
        assert facets_data["links"][0]["text"] == "https://example.com"

    def test_simple_json_includes_facets(self):
        """Test that simple_json output includes facets field"""
        text = "Check https://bsky.app #test"

        # Create link facet
        link_facet = Mock()
        link_facet.index = Mock()
        link_facet.index.byte_start = 6
        link_facet.index.byte_end = 22
        link_feature = MockLinkFeature("https://bsky.app")
        link_facet.features = [link_feature]

        # Create tag facet
        tag_facet = Mock()
        tag_facet.index = Mock()
        tag_facet.index.byte_start = 23
        tag_facet.index.byte_end = 28
        tag_feature = MockTagFeature("test")
        tag_facet.features = [tag_feature]

        mock_post = self.create_mock_post_with_facets(text, [link_facet, tag_facet])

        # Create PostDataList.Item
        item = PostDataList.Item(mock_post)

        # Get simple data
        simple_data = item.get_simple_data()

        # Verify facets field exists
        assert "facets" in simple_data
        assert "links" in simple_data["facets"]
        assert "mentions" in simple_data["facets"]
        assert "tags" in simple_data["facets"]

        # Verify content
        assert len(simple_data["facets"]["links"]) == 1
        assert len(simple_data["facets"]["tags"]) == 1
        assert len(simple_data["facets"]["mentions"]) == 0

    def test_backward_compatibility(self):
        """Test that existing fields remain unchanged"""
        text = "Test post"

        mock_post = self.create_mock_post_with_facets(text, None)

        # Create PostDataList.Item
        item = PostDataList.Item(mock_post)

        # Get simple data
        simple_data = item.get_simple_data()

        # Verify all expected fields exist
        assert "uri" in simple_data
        assert "cid" in simple_data
        assert "author" in simple_data
        assert "text" in simple_data
        assert "created_at" in simple_data
        assert "reply_count" in simple_data
        assert "repost_count" in simple_data
        assert "like_count" in simple_data
        assert "indexed_at" in simple_data
        assert "facets" in simple_data

        # Verify author structure
        assert "did" in simple_data["author"]
        assert "handle" in simple_data["author"]
        assert "display_name" in simple_data["author"]
        assert "avatar" in simple_data["author"]
