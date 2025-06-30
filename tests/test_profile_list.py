import os
import tempfile
import shutil
import json
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from ssky.profile_list import ProfileList
from ssky.util import create_success_response
from atproto_client import models


@pytest.fixture
def mock_profile_list_environment():
    """Fixture for ProfileList tests with mock profiles"""
    test_did1 = "did:plc:test123"
    test_did2 = "did:plc:test456"
    test_handle1 = "test1.bsky.social"
    test_handle2 = "test2.bsky.social"
    
    # Create mock profiles
    mock_profile1 = Mock(spec=models.AppBskyActorDefs.ProfileViewDetailed)
    mock_profile1.did = test_did1
    mock_profile1.handle = test_handle1
    mock_profile1.display_name = "Test User 1"
    mock_profile1.description = "This is a test user description"
    mock_profile1.avatar = "https://example.com/avatar1.jpg"
    mock_profile1.banner = "https://example.com/banner1.jpg"
    mock_profile1.followers_count = 100
    mock_profile1.follows_count = 50
    mock_profile1.posts_count = 25
    mock_profile1.created_at = "2023-01-01T00:00:00.000Z"
    mock_profile1.indexed_at = "2023-01-01T01:00:00.000Z"
    
    mock_profile2 = Mock(spec=models.AppBskyActorDefs.ProfileViewDetailed)
    mock_profile2.did = test_did2
    mock_profile2.handle = test_handle2
    mock_profile2.display_name = "Test User 2"
    mock_profile2.description = None  # Test None description
    mock_profile2.avatar = None
    mock_profile2.banner = None
    mock_profile2.followers_count = 0
    mock_profile2.follows_count = 0
    mock_profile2.posts_count = 0
    mock_profile2.created_at = "2023-02-01T00:00:00.000Z"
    mock_profile2.indexed_at = None
    
    return {
        'test_did1': test_did1,
        'test_did2': test_did2,
        'test_handle1': test_handle1,
        'test_handle2': test_handle2,
        'mock_profile1': mock_profile1,
        'mock_profile2': mock_profile2
    }


class TestProfileList:

    def test_profile_list_basic_operations(self, mock_profile_list_environment):
        """Test basic ProfileList operations"""
        env = mock_profile_list_environment
        profile_list = ProfileList()
        
        # Test initial state
        assert len(profile_list) == 0
        assert str(profile_list) == "[]"
        
        # Test append
        result = profile_list.append(env['test_did1'])
        assert result is profile_list  # Should return self for chaining
        assert len(profile_list) == 1
        assert profile_list[0] == env['test_did1']
        
        # Test append multiple
        profile_list.append(env['test_did2'])
        assert len(profile_list) == 2
        assert profile_list[1] == env['test_did2']
        
        # Test iteration
        dids = list(profile_list)
        assert dids == [env['test_did1'], env['test_did2']]

    def test_profile_list_custom_delimiter(self):
        """Test custom delimiter functionality"""
        # Test class-level delimiter
        original_delimiter = ProfileList.get_default_delimiter()
        ProfileList.set_default_delimiter('|')
        assert ProfileList.get_default_delimiter() == '|'
        
        # Test instance-level delimiter
        profile_list = ProfileList(default_delimiter=',')
        assert profile_list.default_delimiter == ','
        
        # Restore original delimiter
        ProfileList.set_default_delimiter(original_delimiter)

    def test_profile_item_basic_functionality(self, mock_profile_list_environment):
        """Test ProfileList.Item basic functionality"""
        env = mock_profile_list_environment
        item = ProfileList.Item(env['mock_profile1'])
        
        # Test id
        assert item.id() == env['test_did1']
        
        # Test text_only
        assert item.text_only() == "This is a test user description"
        
        # Test with None description
        item2 = ProfileList.Item(env['mock_profile2'])
        assert item2.text_only() == ""

    def test_profile_item_short_format(self, mock_profile_list_environment):
        """Test ProfileList.Item short format"""
        env = mock_profile_list_environment
        item = ProfileList.Item(env['mock_profile1'])
        
        # Test default delimiter
        short_output = item.short()
        expected_parts = [
            env['test_did1'],
            env['test_handle1'],
            "Test_User_1",  # summarize converts spaces to underscores
            "This_is_a_test_user_description"  # summarize converts spaces to underscores
        ]
        assert short_output == " ".join(expected_parts)
        
        # Test custom delimiter
        short_output_custom = item.short(delimiter="|")
        assert short_output_custom == "|".join(expected_parts)

    def test_profile_item_long_format(self, mock_profile_list_environment):
        """Test ProfileList.Item long format"""
        env = mock_profile_list_environment
        item = ProfileList.Item(env['mock_profile1'])
        long_output = item.long()
        
        expected_lines = [
            "Created-At: 2023-01-01T00:00:00.000Z",
            "DID: did:plc:test123",
            "Display-Name: Test User 1",
            "Handle: test1.bsky.social",
            "",
            "This is a test user description"
        ]
        assert long_output == "\n".join(expected_lines)

    def test_profile_item_json_format(self, mock_profile_list_environment):
        """Test ProfileList.Item JSON format"""
        env = mock_profile_list_environment
        item = ProfileList.Item(env['mock_profile1'])
        
        with patch('atproto_client.models.utils.get_model_as_json') as mock_json:
            mock_json.return_value = '{"test": "json"}'
            json_output = item.json()
            assert json_output == '{"test": "json"}'
            mock_json.assert_called_once_with(env['mock_profile1'])

    def test_profile_item_simple_json_format(self, mock_profile_list_environment):
        """Test ProfileList.Item simple JSON format"""
        env = mock_profile_list_environment
        item = ProfileList.Item(env['mock_profile1'])
        simple_json_output = item.simple_json()
        
        # Parse the JSON to verify structure
        parsed = json.loads(simple_json_output)
        assert parsed["status"] == "ok"
        assert "data" in parsed
        
        data = parsed["data"]
        assert data["did"] == env['test_did1']
        assert data["handle"] == env['test_handle1']
        assert data["display_name"] == "Test User 1"
        assert data["description"] == "This is a test user description"
        assert data["followers_count"] == 100
        assert data["follows_count"] == 50
        assert data["posts_count"] == 25

    def test_profile_item_simple_json_with_none_values(self, mock_profile_list_environment):
        """Test ProfileList.Item simple JSON with None values"""
        env = mock_profile_list_environment
        item = ProfileList.Item(env['mock_profile2'])
        simple_json_output = item.simple_json()
        
        parsed = json.loads(simple_json_output)
        data = parsed["data"]
        assert data["description"] == ""  # None should become empty string
        assert data["banner"] is None
        assert data["indexed_at"] is None

    def test_profile_item_printable_formats(self, mock_profile_list_environment):
        """Test ProfileList.Item printable method with different formats"""
        env = mock_profile_list_environment
        item = ProfileList.Item(env['mock_profile1'])
        
        # Test id format
        assert item.printable('id') == env['test_did1']
        
        # Test long format
        long_output = item.printable('long')
        assert "Created-At: 2023-01-01T00:00:00.000Z" in long_output
        
        # Test text format
        assert item.printable('text') == "This is a test user description"
        
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
        assert env['test_did1'] in short_output
        assert env['test_handle1'] in short_output

    def test_profile_item_filename_generation(self, mock_profile_list_environment):
        """Test ProfileList.Item filename generation"""
        env = mock_profile_list_environment
        item = ProfileList.Item(env['mock_profile1'])
        filename = item.get_filename()
        assert filename == "test1.bsky.social.txt"

    def test_profile_list_update_with_mock_session(self, mock_profile_list_environment):
        """Test ProfileList update method with mocked session"""
        env = mock_profile_list_environment
        profile_list = ProfileList()
        profile_list.append(env['test_did1'])
        profile_list.append(env['test_did2'])
        
        # Mock SskySession and client
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client
        
        # Mock get_profiles response
        mock_response = Mock()
        mock_response.profiles = [env['mock_profile1'], env['mock_profile2']]
        mock_client.get_profiles.return_value = mock_response
        
        with patch('ssky.profile_list.SskySession') as mock_session_class:
            mock_session_class.return_value = mock_session
            
            # Test update
            result = profile_list.update()
            assert result is profile_list  # Should return self
            assert profile_list.items is not None
            assert len(profile_list.items) == 2
            
            # Verify get_profiles was called with correct DIDs
            mock_client.get_profiles.assert_called_once_with([env['test_did1'], env['test_did2']])

    def test_profile_list_update_large_list(self):
        """Test ProfileList update with more than 25 items (pagination)"""
        profile_list = ProfileList()
        
        # Add 30 DIDs to test pagination
        test_dids = [f"did:plc:test{i:03d}" for i in range(30)]
        for did in test_dids:
            profile_list.append(did)
        
        # Mock session and client
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client
        
        # Mock profiles for responses
        mock_profiles_1 = [Mock() for _ in range(25)]
        mock_profiles_2 = [Mock() for _ in range(5)]
        
        mock_response_1 = Mock()
        mock_response_1.profiles = mock_profiles_1
        mock_response_2 = Mock()
        mock_response_2.profiles = mock_profiles_2
        
        mock_client.get_profiles.side_effect = [mock_response_1, mock_response_2]
        
        with patch('ssky.profile_list.SskySession') as mock_session_class:
            mock_session_class.return_value = mock_session
            
            profile_list.update()
            
            # Should make 2 calls for pagination
            assert mock_client.get_profiles.call_count == 2
            
            # Verify call arguments
            call_args_list = mock_client.get_profiles.call_args_list
            assert call_args_list[0][0][0] == test_dids[:25]  # First 25
            assert call_args_list[1][0][0] == test_dids[25:]  # Last 5

    def test_profile_list_print_console_output(self, mock_profile_list_environment):
        """Test ProfileList print method for console output"""
        env = mock_profile_list_environment
        profile_list = ProfileList()
        profile_list.items = [
            ProfileList.Item(env['mock_profile1']),
            ProfileList.Item(env['mock_profile2'])
        ]
        
        # Test simple_json format (special case)
        with patch('builtins.print') as mock_print:
            profile_list.print('simple_json')
            
            # Should print a single JSON response with all profiles
            mock_print.assert_called_once()
            printed_content = mock_print.call_args[0][0]
            parsed = json.loads(printed_content)
            assert parsed["status"] == "ok"
            assert len(parsed["data"]) == 2
        
        # Test other formats
        with patch('builtins.print') as mock_print:
            profile_list.print('short')
            
            # Should print each item individually
            assert mock_print.call_count == 2

    def test_profile_list_print_long_format_with_separator(self, mock_profile_list_environment):
        """Test ProfileList print method with long format separator"""
        env = mock_profile_list_environment
        profile_list = ProfileList()
        profile_list.items = [
            ProfileList.Item(env['mock_profile1']),
            ProfileList.Item(env['mock_profile2'])
        ]
        
        with patch('builtins.print') as mock_print:
            profile_list.print('long')
            
            # Should print: item1, separator, item2
            assert mock_print.call_count == 3
            # Check that separator was printed
            separator_call = mock_print.call_args_list[1]
            assert separator_call[0][0] == '----------------'

    def test_profile_list_print_file_output(self, mock_profile_list_environment):
        """Test ProfileList print method for file output"""
        env = mock_profile_list_environment
        profile_list = ProfileList()
        profile_list.items = [
            ProfileList.Item(env['mock_profile1']),
            ProfileList.Item(env['mock_profile2'])
        ]
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_list.print('short', output=temp_dir)
            
            # Check that files were created
            expected_files = [
                "test1.bsky.social.txt",
                "test2.bsky.social.txt"
            ]
            
            for filename in expected_files:
                filepath = os.path.join(temp_dir, filename)
                assert os.path.exists(filepath)
                
                # Check file content
                with open(filepath, 'r') as f:
                    content = f.read().strip()
                    if filename == "test1.bsky.social.txt":
                        assert env['test_did1'] in content
                        assert env['test_handle1'] in content
                    else:
                        assert env['test_did2'] in content
                        assert env['test_handle2'] in content

    def test_profile_list_print_file_output_with_custom_delimiter(self, mock_profile_list_environment):
        """Test ProfileList print method for file output with custom delimiter"""
        env = mock_profile_list_environment
        profile_list = ProfileList()
        profile_list.items = [ProfileList.Item(env['mock_profile1'])]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_list.print('short', output=temp_dir, delimiter='|')
            
            filepath = os.path.join(temp_dir, "test1.bsky.social.txt")
            with open(filepath, 'r') as f:
                content = f.read().strip()
                # Should use custom delimiter
                assert '|' in content
                assert env['test_did1'] in content

    def test_profile_list_edge_cases(self, mock_profile_list_environment):
        """Test ProfileList edge cases"""
        env = mock_profile_list_environment
        # Test empty list
        empty_list = ProfileList()
        assert len(empty_list) == 0
        
        # Test update on empty list
        with patch('ssky.profile_list.SskySession'):
            result = empty_list.update()
            assert result is empty_list
            assert empty_list.items == []
        
        # Test multiple updates (should not duplicate items)
        profile_list = ProfileList()
        profile_list.append(env['test_did1'])
        
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client
        mock_response = Mock()
        mock_response.profiles = [env['mock_profile1']]
        mock_client.get_profiles.return_value = mock_response
        
        with patch('ssky.profile_list.SskySession') as mock_session_class:
            mock_session_class.return_value = mock_session
            
            # First update
            profile_list.update()
            first_items_count = len(profile_list.items)
            
            # Second update should not call API again
            profile_list.update()
            assert len(profile_list.items) == first_items_count
            assert mock_client.get_profiles.call_count == 1  # Called only once 