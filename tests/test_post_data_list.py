import os
import tempfile
import json
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from ssky.post_data_list import PostDataList
from atproto_client import models


@pytest.fixture
def mock_post_data_environment():
    """Fixture for PostDataList tests with mock posts"""
    test_uri1 = "at://did:plc:test123/app.bsky.feed.post/test1"
    test_uri2 = "at://did:plc:test456/app.bsky.feed.post/test2"
    test_cid1 = "bafyreicid1"
    test_cid2 = "bafyreicid2"
    
    # Create mock posts
    mock_post1 = Mock(spec=models.AppBskyFeedDefs.PostView)
    mock_post1.uri = test_uri1
    mock_post1.cid = test_cid1
    
    # Mock author
    mock_author1 = Mock()
    mock_author1.did = "did:plc:test123"
    mock_author1.handle = "test1.bsky.social"
    mock_author1.display_name = "Test User 1"
    mock_author1.avatar = "https://example.com/avatar1.jpg"
    mock_post1.author = mock_author1
    
    # Mock record
    mock_record1 = Mock()
    mock_record1.text = "This is a test post"
    mock_record1.created_at = "2023-01-01T00:00:00.000Z"
    mock_record1.facets = None  # No facets for simple test
    mock_post1.record = mock_record1
    
    # Mock indexed_at
    mock_post1.indexed_at = "2023-01-01T01:00:00.000Z"
    
    # Mock reply_count, repost_count, like_count
    mock_post1.reply_count = 5
    mock_post1.repost_count = 10
    mock_post1.like_count = 15
    mock_post1.viewer = None  # No viewer info for simple test
    
    # Create second mock post
    mock_post2 = Mock(spec=models.AppBskyFeedDefs.PostView)
    mock_post2.uri = test_uri2
    mock_post2.cid = test_cid2
    
    mock_author2 = Mock()
    mock_author2.did = "did:plc:test456"
    mock_author2.handle = "test2.bsky.social"
    mock_author2.display_name = "Test User 2"
    mock_author2.avatar = "https://example.com/avatar2.jpg"
    mock_post2.author = mock_author2
    
    mock_record2 = Mock()
    mock_record2.text = "Another test post"
    mock_record2.created_at = "2023-02-01T00:00:00.000Z"
    mock_record2.facets = None  # No facets for simple test
    mock_post2.record = mock_record2
    
    mock_post2.indexed_at = "2023-02-01T01:00:00.000Z"
    mock_post2.reply_count = 0
    mock_post2.repost_count = 0
    mock_post2.like_count = 0
    mock_post2.viewer = None  # No viewer info for simple test
    
    return {
        'test_uri1': test_uri1,
        'test_uri2': test_uri2,
        'test_cid1': test_cid1,
        'test_cid2': test_cid2,
        'mock_post1': mock_post1,
        'mock_post2': mock_post2,
        'mock_author1': mock_author1,
        'mock_author2': mock_author2,
        'mock_record1': mock_record1,
        'mock_record2': mock_record2,
    }


class TestPostDataList:

    def test_post_data_list_basic_operations(self, mock_post_data_environment):
        """Test basic PostDataList operations"""
        env = mock_post_data_environment
        post_list = PostDataList()
        
        # Test initial state
        assert len(post_list) == 0
        assert str(post_list) == "[]"
        
        # Test append
        result = post_list.append(env['mock_post1'])
        assert result is post_list  # Should return self for chaining
        assert len(post_list) == 1
        assert post_list[0] == env['mock_post1']
        
        # Test append multiple
        post_list.append(env['mock_post2'])
        assert len(post_list) == 2
        assert post_list[1] == env['mock_post2']
        
        # Test iteration
        posts = list(post_list)
        assert posts == [env['mock_post1'], env['mock_post2']]

    def test_post_data_list_custom_delimiter(self):
        """Test custom delimiter functionality"""
        # Test class-level delimiter
        original_delimiter = PostDataList.get_default_delimiter()
        PostDataList.set_default_delimiter('|')
        assert PostDataList.get_default_delimiter() == '|'
        
        # Test instance-level delimiter
        post_list = PostDataList(default_delimiter=',')
        assert post_list.default_delimiter == ','
        
        # Restore original delimiter
        PostDataList.set_default_delimiter(original_delimiter)

    def test_post_data_list_duplicate_handling(self, mock_post_data_environment):
        """Test PostDataList duplicate handling"""
        env = mock_post_data_environment
        post_list = PostDataList()
        
        # Add same post twice
        post_list.append(env['mock_post1'])
        post_list.append(env['mock_post1'])
        
        # Should only contain one instance
        assert len(post_list) == 1
        assert post_list[0] == env['mock_post1']

    def test_post_item_basic_functionality(self, mock_post_data_environment):
        """Test PostDataList.Item basic functionality"""
        env = mock_post_data_environment
        item = PostDataList.Item(env['mock_post1'])
        
        # Test id (should return URI::CID format)
        expected_id = f"{env['test_uri1']}::{env['test_cid1']}"
        assert item.id() == expected_id
        
        # Test text_only
        assert item.text_only() == "This is a test post"

    def test_post_item_short_format(self, mock_post_data_environment):
        """Test PostDataList.Item short format"""
        env = mock_post_data_environment
        item = PostDataList.Item(env['mock_post1'])
        
        # Test default delimiter
        short_output = item.short()
        expected_parts = [
            f"{env['test_uri1']}::{env['test_cid1']}",  # URI::CID format
            "did:plc:test123",  # author DID
            "test1.bsky.social",  # author handle
            "Test_User_1",  # summarized display name
            "This_is_a_test_post"  # summarized text
        ]
        assert short_output == " ".join(expected_parts)
        
        # Test custom delimiter
        short_output_custom = item.short(delimiter="|")
        assert short_output_custom == "|".join(expected_parts)

    def test_post_item_long_format(self, mock_post_data_environment):
        """Test PostDataList.Item long format"""
        env = mock_post_data_environment
        item = PostDataList.Item(env['mock_post1'])
        long_output = item.long()
        
        expected_lines = [
            "Author-DID: did:plc:test123",
            "Author-Display-Name: Test User 1",
            "Author-Handle: test1.bsky.social",
            "Created-At: 2023-01-01T00:00:00.000Z",
            "Record-CID: bafyreicid1",
            "Record-URI: at://did:plc:test123/app.bsky.feed.post/test1",
            "",
            "This is a test post"
        ]
        assert long_output == "\n".join(expected_lines)

    def test_post_item_json_format(self, mock_post_data_environment):
        """Test PostDataList.Item JSON format"""
        env = mock_post_data_environment
        item = PostDataList.Item(env['mock_post1'])
        
        with patch('atproto_client.models.utils.get_model_as_json') as mock_json:
            mock_json.return_value = '{"test": "json"}'
            json_output = item.json()
            assert json_output == '{"test": "json"}'
            mock_json.assert_called_once_with(env['mock_post1'])

    def test_post_item_simple_json_format(self, mock_post_data_environment):
        """Test PostDataList.Item simple JSON format"""
        env = mock_post_data_environment
        item = PostDataList.Item(env['mock_post1'])
        simple_json_output = item.simple_json()
        
        # Parse the JSON to verify structure
        parsed = json.loads(simple_json_output)
        assert parsed["status"] == "ok"
        assert "data" in parsed
        
        data = parsed["data"]
        assert data["uri"] == env['test_uri1']
        assert data["cid"] == env['test_cid1']
        assert data["author"]["handle"] == "test1.bsky.social"
        assert data["author"]["display_name"] == "Test User 1"
        assert data["text"] == "This is a test post"
        assert data["created_at"] == "2023-01-01T00:00:00.000Z"
        assert data["indexed_at"] == "2023-01-01T01:00:00.000Z"
        assert data["reply_count"] == 5
        assert data["repost_count"] == 10
        assert data["like_count"] == 15

    def test_post_item_printable_formats(self, mock_post_data_environment):
        """Test PostDataList.Item printable method with different formats"""
        env = mock_post_data_environment
        item = PostDataList.Item(env['mock_post1'])
        
        # Test id format
        expected_id = f"{env['test_uri1']}::{env['test_cid1']}"
        assert item.printable('id') == expected_id
        
        # Test long format
        long_output = item.printable('long')
        assert "Author-DID: did:plc:test123" in long_output
        
        # Test text format
        assert item.printable('text') == "This is a test post"
        
        # Test json format
        with patch('atproto_client.models.utils.get_model_as_json') as mock_json:
            mock_json.return_value = '{"test": "json"}'
            assert item.printable('json') == '{"test": "json"}'
        
        # Test simple_json format
        simple_json_output = item.printable('simple_json')
        parsed = json.loads(simple_json_output)
        assert parsed["status"] == "ok"
        
        # Test default (short) format
        short_output = item.printable('short')
        assert env['test_uri1'] in short_output
        assert "test1.bsky.social" in short_output

    def test_post_item_filename_generation(self, mock_post_data_environment):
        """Test PostDataList.Item filename generation"""
        env = mock_post_data_environment
        item = PostDataList.Item(env['mock_post1'])
        filename = item.get_filename()
        # Should use handle.datetime.txt format
        expected_filename = "test1.bsky.social.20230101000000.txt"
        assert filename == expected_filename





    def test_post_data_list_print_console_output(self, mock_post_data_environment):
        """Test PostDataList print method for console output"""
        env = mock_post_data_environment
        post_list = PostDataList()
        post_list.items = [
            PostDataList.Item(env['mock_post1']),
            PostDataList.Item(env['mock_post2'])
        ]
        
        # Test simple_json format (special case)
        with patch('builtins.print') as mock_print:
            post_list.print('simple_json')
            
            # Should print a single JSON response with all posts
            mock_print.assert_called_once()
            printed_content = mock_print.call_args[0][0]
            parsed = json.loads(printed_content)
            assert parsed["status"] == "ok"
            assert len(parsed["data"]) == 2

    def test_post_data_list_print_long_format_with_separator(self, mock_post_data_environment):
        """Test PostDataList print method with long format separator"""
        env = mock_post_data_environment
        post_list = PostDataList()
        post_list.items = [
            PostDataList.Item(env['mock_post1']),
            PostDataList.Item(env['mock_post2'])
        ]
        
        with patch('builtins.print') as mock_print:
            post_list.print('long')
            
            # Should print: item1, separator, item2
            assert mock_print.call_count == 3
            # Check that separator was printed
            separator_call = mock_print.call_args_list[1]
            assert separator_call[0][0] == '----------------'

    def test_post_data_list_print_file_output(self, mock_post_data_environment):
        """Test PostDataList print method for file output"""
        env = mock_post_data_environment
        post_list = PostDataList()
        post_list.items = [
            PostDataList.Item(env['mock_post1']),
            PostDataList.Item(env['mock_post2'])
        ]
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            post_list.print('short', output=temp_dir)
            
            # Check that files were created
            expected_files = [
                "test1.bsky.social.20230101000000.txt",
                "test2.bsky.social.20230201000000.txt"
            ]
            
            for filename in expected_files:
                filepath = os.path.join(temp_dir, filename)
                assert os.path.exists(filepath)
                
                # Check file content
                with open(filepath, 'r') as f:
                    content = f.read().strip()
                    if filename == "test1.bsky.social.20230101000000.txt":
                        assert env['test_uri1'] in content
                        assert "test1.bsky.social" in content
                        assert "This_is_a_test_post" in content  # summarized text
                    else:
                        assert env['test_uri2'] in content
                        assert "test2.bsky.social" in content
                        assert "Another_test_post" in content  # summarized text

    def test_post_data_list_print_file_output_with_custom_delimiter(self, mock_post_data_environment):
        """Test PostDataList print method for file output with custom delimiter"""
        env = mock_post_data_environment
        post_list = PostDataList()
        post_list.items = [PostDataList.Item(env['mock_post1'])]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_list.print('short', output=temp_dir, delimiter='|')
            
            filepath = os.path.join(temp_dir, "test1.bsky.social.20230101000000.txt")
            with open(filepath, 'r') as f:
                content = f.read().strip()
                # Should use custom delimiter
                assert '|' in content
                assert env['test_uri1'] in content

    def test_post_data_list_edge_cases(self, mock_post_data_environment):
        """Test PostDataList edge cases"""
        env = mock_post_data_environment
        # Test empty list
        empty_list = PostDataList()
        assert len(empty_list) == 0
        
        # Test multiple appends of same item (should not duplicate)
        post_list = PostDataList()
        post_list.append(env['mock_post1'])
        post_list.append(env['mock_post1'])  # Same post again
        
        # Should only contain one instance
        assert len(post_list) == 1

    def test_post_item_with_missing_attributes(self, mock_post_data_environment):
        """Test PostDataList.Item with missing attributes"""
        env = mock_post_data_environment
        # Create mock post with minimal attributes
        minimal_post = Mock()
        minimal_post.uri = env['test_uri1']
        minimal_post.cid = env['test_cid1']
        
        # Mock author with minimal info
        minimal_author = Mock()
        minimal_author.did = "did:plc:minimal123"
        minimal_author.handle = "minimal.bsky.social"
        minimal_author.display_name = None
        minimal_author.avatar = None
        minimal_post.author = minimal_author
        
        # Mock record with minimal info
        minimal_record = Mock()
        minimal_record.text = "Minimal post"
        minimal_record.created_at = "2023-01-01T00:00:00.000Z"
        minimal_record.facets = None
        minimal_post.record = minimal_record
        
        minimal_post.indexed_at = None
        minimal_post.reply_count = None
        minimal_post.repost_count = None
        minimal_post.like_count = None
        
        item = PostDataList.Item(minimal_post)
        
        # Test that it handles None values gracefully
        simple_json_output = item.simple_json()
        parsed = json.loads(simple_json_output)
        data = parsed["data"]
        
        assert data["author"]["display_name"] is None
        assert data["indexed_at"] is None
        assert data["reply_count"] is None
        assert data["repost_count"] is None
        assert data["like_count"] is None

    def test_post_item_facets_url_processing(self, mock_post_data_environment):
        """Test PostDataList.Item URL processing from facets"""
        env = mock_post_data_environment
        # Create mock post with facets containing URL
        faceted_post = Mock()
        faceted_post.uri = env['test_uri1']
        faceted_post.cid = env['test_cid1']
        
        # Mock author
        faceted_author = Mock()
        faceted_author.did = "did:plc:test123"
        faceted_author.handle = "test.bsky.social"
        faceted_author.display_name = "Test User"
        faceted_author.avatar = None
        faceted_post.author = faceted_author
        
        # Mock record with truncated URL and facets
        faceted_record = Mock()
        faceted_record.text = "Check out this link: example.com/..."
        faceted_record.created_at = "2023-01-01T00:00:00.000Z"
        
        # Mock facets with URL restoration info
        mock_facet = Mock()
        mock_facet.index = Mock()
        mock_facet.index.byte_start = 23  # Position of "example.com/..."
        mock_facet.index.byte_end = 37    # End of truncated text
        
        mock_feature = Mock()
        mock_feature.uri = "https://example.com/full-url-path"
        mock_facet.features = [mock_feature]
        
        faceted_record.facets = [mock_facet]
        faceted_post.record = faceted_record
        
        # Mock other attributes
        faceted_post.indexed_at = "2023-01-01T01:00:00.000Z"
        faceted_post.reply_count = 0
        faceted_post.repost_count = 0
        faceted_post.like_count = 0
        faceted_post.viewer = None
        
        item = PostDataList.Item(faceted_post)
        
        # Test that text_only processes URLs from facets
        processed_text = item.text_only()
        assert "https://example.com/full-url-path" in processed_text
        assert "example.com/..." not in processed_text
        
        # Test that simple_json also includes processed text
        simple_json_output = item.simple_json()
        parsed = json.loads(simple_json_output)
        data = parsed["data"]
        assert "https://example.com/full-url-path" in data["text"]

    def test_post_item_facets_no_facets(self, mock_post_data_environment):
        """Test PostDataList.Item with no facets (should return original text)"""
        env = mock_post_data_environment
        item = PostDataList.Item(env['mock_post1'])
        
        # Should return original text when no facets
        assert item.text_only() == "This is a test post"

    def test_post_item_facets_empty_facets(self, mock_post_data_environment):
        """Test PostDataList.Item with empty facets list"""
        env = mock_post_data_environment
        # Create post with empty facets
        post_with_empty_facets = Mock()
        post_with_empty_facets.uri = env['test_uri1']
        post_with_empty_facets.cid = env['test_cid1']
        post_with_empty_facets.author = env['mock_author1']
        
        record_with_empty_facets = Mock()
        record_with_empty_facets.text = "No URLs here"
        record_with_empty_facets.created_at = "2023-01-01T00:00:00.000Z"
        record_with_empty_facets.facets = []  # Empty list
        post_with_empty_facets.record = record_with_empty_facets
        
        post_with_empty_facets.indexed_at = None
        post_with_empty_facets.reply_count = 0
        post_with_empty_facets.repost_count = 0
        post_with_empty_facets.like_count = 0
        post_with_empty_facets.viewer = None
        
        item = PostDataList.Item(post_with_empty_facets)
        
        # Should return original text
        assert item.text_only() == "No URLs here"

    def test_post_item_facets_non_url_facets(self, mock_post_data_environment):
        """Test PostDataList.Item with facets that are not URLs (mentions, tags)"""
        env = mock_post_data_environment
        # Create post with mention facets (should be ignored)
        post_with_mentions = Mock()
        post_with_mentions.uri = env['test_uri1']
        post_with_mentions.cid = env['test_cid1']
        post_with_mentions.author = env['mock_author1']
        
        mention_record = Mock()
        mention_record.text = "Hello @user this is a mention"
        mention_record.created_at = "2023-01-01T00:00:00.000Z"
        
        # Mock mention facet (should be ignored by URL processing)
        mock_mention_facet = Mock()
        mock_mention_facet.index = Mock()
        mock_mention_facet.index.byte_start = 6
        mock_mention_facet.index.byte_end = 11
        
        mock_mention_feature = Mock(spec=[])  # Empty spec means no attributes
        # Mention features don't have 'uri' attribute, they have 'did'
        mock_mention_feature.did = "did:plc:mentioned-user"
        mock_mention_facet.features = [mock_mention_feature]
        
        mention_record.facets = [mock_mention_facet]
        post_with_mentions.record = mention_record
        
        post_with_mentions.indexed_at = None
        post_with_mentions.reply_count = 0
        post_with_mentions.repost_count = 0
        post_with_mentions.like_count = 0
        post_with_mentions.viewer = None
        
        item = PostDataList.Item(post_with_mentions)
        
        # Should return original text since mention facets are ignored
        assert item.text_only() == "Hello @user this is a mention"

    def test_post_item_facets_multiple_urls(self, mock_post_data_environment):
        """Test PostDataList.Item with multiple URL facets"""
        env = mock_post_data_environment
        # Create post with multiple URLs
        multi_url_post = Mock()
        multi_url_post.uri = env['test_uri1']
        multi_url_post.cid = env['test_cid1']
        multi_url_post.author = env['mock_author1']
        
        multi_url_record = Mock()
        multi_url_record.text = "Visit example.com/... and also check.com/..."
        multi_url_record.created_at = "2023-01-01T00:00:00.000Z"
        
        # Mock first URL facet
        mock_facet1 = Mock()
        mock_facet1.index = Mock()
        mock_facet1.index.byte_start = 6   # Position of first "example.com/..."
        mock_facet1.index.byte_end = 20    # End of first truncated URL
        
        mock_feature1 = Mock()
        mock_feature1.uri = "https://example.com/full-path"
        mock_facet1.features = [mock_feature1]
        
        # Mock second URL facet
        mock_facet2 = Mock()
        mock_facet2.index = Mock()
        mock_facet2.index.byte_start = 35  # Position of second "check.com/..."
        mock_facet2.index.byte_end = 47    # End of second truncated URL
        
        mock_feature2 = Mock()
        mock_feature2.uri = "https://check.com/another-path"
        mock_facet2.features = [mock_feature2]
        
        multi_url_record.facets = [mock_facet1, mock_facet2]
        multi_url_post.record = multi_url_record
        
        multi_url_post.indexed_at = None
        multi_url_post.reply_count = 0
        multi_url_post.repost_count = 0
        multi_url_post.like_count = 0
        multi_url_post.viewer = None
        
        item = PostDataList.Item(multi_url_post)
        
        # Test that both URLs are processed
        processed_text = item.text_only()
        assert "https://example.com/full-path" in processed_text
        assert "https://check.com/another-path" in processed_text
        assert "example.com/..." not in processed_text
        assert "check.com/..." not in processed_text

    def test_post_item_facets_mixed_features(self, mock_post_data_environment):
        """Test PostDataList.Item with mixed facet features (URL + mention)"""
        env = mock_post_data_environment
        # Create post with both URL and mention in same facet
        mixed_post = Mock()
        mixed_post.uri = env['test_uri1']
        mixed_post.cid = env['test_cid1']
        mixed_post.author = env['mock_author1']
        
        mixed_record = Mock()
        mixed_record.text = "Check example.com/... and @user"
        mixed_record.created_at = "2023-01-01T00:00:00.000Z"
        
        # Mock facet with URL feature
        mock_url_facet = Mock()
        mock_url_facet.index = Mock()
        mock_url_facet.index.byte_start = 6
        mock_url_facet.index.byte_end = 20
        
        mock_url_feature = Mock()
        mock_url_feature.uri = "https://example.com/full-url"
        mock_url_facet.features = [mock_url_feature]
        
        # Mock facet with mention feature
        mock_mention_facet = Mock()
        mock_mention_facet.index = Mock()
        mock_mention_facet.index.byte_start = 25
        mock_mention_facet.index.byte_end = 30
        
        mock_mention_feature = Mock(spec=[])  # Empty spec means no attributes
        mock_mention_feature.did = "did:plc:user123"
        mock_mention_facet.features = [mock_mention_feature]
        
        mixed_record.facets = [mock_url_facet, mock_mention_facet]
        mixed_post.record = mixed_record
        
        mixed_post.indexed_at = None
        mixed_post.reply_count = 0
        mixed_post.repost_count = 0
        mixed_post.like_count = 0
        mixed_post.viewer = None
        
        item = PostDataList.Item(mixed_post)
        
        # Test that only URL is processed, mention is left as-is
        processed_text = item.text_only()
        assert "https://example.com/full-url" in processed_text
        assert "@user" in processed_text  # Mention should remain unchanged
        assert "example.com/..." not in processed_text

    def test_post_item_facets_unicode_handling(self, mock_post_data_environment):
        """Test PostDataList.Item facets with Unicode text"""
        env = mock_post_data_environment
        # Create post with Unicode characters and URL
        unicode_post = Mock()
        unicode_post.uri = env['test_uri1']
        unicode_post.cid = env['test_cid1']
        unicode_post.author = env['mock_author1']
        
        unicode_record = Mock()
        unicode_record.text = "こんにちは example.com/... 世界"
        unicode_record.created_at = "2023-01-01T00:00:00.000Z"
        
        # Mock facet with URL (note: byte positions must account for UTF-8 encoding)
        mock_facet = Mock()
        mock_facet.index = Mock()
        # "こんにちは " is 18 bytes in UTF-8 (6 chars × 3 bytes each)
        mock_facet.index.byte_start = 18
        mock_facet.index.byte_end = 32  # "example.com/..." is 14 bytes
        
        mock_feature = Mock()
        mock_feature.uri = "https://example.com/unicode-test"
        mock_facet.features = [mock_feature]
        
        unicode_record.facets = [mock_facet]
        unicode_post.record = unicode_record
        
        unicode_post.indexed_at = None
        unicode_post.reply_count = 0
        unicode_post.repost_count = 0
        unicode_post.like_count = 0
        unicode_post.viewer = None
        
        item = PostDataList.Item(unicode_post)
        
        # Test that Unicode text is handled correctly
        processed_text = item.text_only()
        assert "こんにちは" in processed_text
        assert "世界" in processed_text
        assert "https://example.com/unicode-test" in processed_text
        assert "example.com/..." not in processed_text

 