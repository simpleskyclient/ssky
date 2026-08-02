"""Unit tests for SIGPIPE handling and clean pipe early termination."""

import os
import signal
import sys
import subprocess
from unittest.mock import patch, MagicMock
import pytest

from ssky.main import execute, main


def test_sigpipe_handler_setup():
    """Verify that signal.SIGPIPE is restored to SIG_DFL on supported platforms."""
    if not hasattr(signal, 'SIGPIPE'):
        pytest.skip("SIGPIPE is not supported on this platform")

    code = (
        "import signal, sys; "
        "from ssky.main import setup; "
        "setup(); "
        "handler = signal.getsignal(signal.SIGPIPE); "
        "sys.exit(0 if handler == signal.SIG_DFL else 1)"
    )
    res = subprocess.run([sys.executable, "-c", code])
    assert res.returncode == 0


def test_execute_handles_broken_pipe():
    """Verify execute() returns exit code 141 and suppresses traceback on BrokenPipeError."""
    args = MagicMock()
    args.format = 'short'
    args.output = None
    args.delimiter = ' '

    mock_func = MagicMock(side_effect=BrokenPipeError("Broken pipe"))
    with patch('ssky.main.import_module') as mock_import:
        mock_module = MagicMock()
        mock_module.get = mock_func
        mock_import.return_value = mock_module

        result = execute('get', args)
        assert result == 141


def test_main_returns_sigpipe_exit_code():
    """Verify main() returns 141 when execute() returns 141."""
    with patch('ssky.main.setup'), \
         patch('ssky.main.parse', return_value=('get', MagicMock())), \
         patch('ssky.main.execute', return_value=141):
        assert main() == 141


def test_cli_sigpipe_subshell():
    """Integration check: early exit in pipe produces no traceback on stderr."""
    code = (
        "import sys, signal; "
        "from ssky.main import setup; "
        "setup(); "
        "[print(f'item {i}') for i in range(100000)]"
    )
    proc = subprocess.Popen(
        f"{sys.executable} -c \"{code}\" | head -n 1",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate()
    assert stderr == ''
