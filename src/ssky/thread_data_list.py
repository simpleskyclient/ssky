import os
import sys
from ssky.thread_data import ThreadData


class ThreadDataList:
    """
    Represents a list of threads.
    """

    def __init__(self):
        """Initialize empty thread list."""
        self.threads = []  # List of ThreadData objects

    def append(self, thread_data):
        """
        Add a ThreadData to the list.

        Args:
            thread_data: ThreadData object
        """
        if isinstance(thread_data, ThreadData):
            self.threads.append(thread_data)

    def print(self, format='', output=None, delimiter=' '):
        """
        Print all threads in specified format.

        Args:
            format: Output format ('id', 'text', 'long', 'json', 'simple_json', or '' for short)
            output: Output directory path for file output
            delimiter: Delimiter for short format
        """
        if output:
            self._print_to_files(format, output, delimiter)
        else:
            self._print_to_stdout(format, delimiter)

    def _print_to_stdout(self, format, delimiter):
        """Print all threads to stdout."""
        for idx, thread in enumerate(self.threads):
            # Print thread
            thread.print(format=format, delimiter=delimiter)

            # Add separator between threads (for long/text format only, not for short/id)
            if idx < len(self.threads) - 1 and format in ('long', 'text'):
                print("----------------")

    def _print_to_files(self, format, output_dir, delimiter):
        """
        Print all threads to files.

        Args:
            format: Output format
            output_dir: Output directory path
            delimiter: Delimiter for short format
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Each thread is saved to its own file
        for thread in self.threads:
            thread.print(format=format, output=output_dir, delimiter=delimiter)
