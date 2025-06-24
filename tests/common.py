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

def teardown():
    pass

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

def cleanup_session_file():
    """Clean up session file"""
    session_path = os.path.expanduser('~/.ssky')
    if os.path.exists(session_path):
        os.remove(session_path)

def create_mock_atproto_client():
    """Create mock atproto client for testing without API calls"""
    mock_client = Mock()
    mock_profile = Mock()
    mock_profile.did = "did:plc:test123456789"
    
    # Mock successful login
    mock_client.login.return_value = mock_profile
    mock_client.export_session_string.return_value = '{"test": "session_data"}'
    
    return mock_client, mock_profile