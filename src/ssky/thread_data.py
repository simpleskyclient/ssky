import os
import sys
from atproto import models


class ThreadData:
    """
    Represents a single thread with its posts.
    """

    def __init__(self, thread_view):
        """
        Initialize thread from AT Protocol thread view.

        Args:
            thread_view: models.AppBskyFeedGetPostThread.Response
        """
        self.posts = []  # List of (post, depth) tuples
        self._flatten(thread_view.thread, depth=0)

    def _flatten(self, thread_node, depth=0):
        """
        Recursively flatten thread structure into list of posts with depth.

        Args:
            thread_node: Thread node (ThreadViewPost or NotFoundPost or BlockedPost)
            depth: Current depth in thread
        """
        # Handle different thread node types
        if isinstance(thread_node, models.AppBskyFeedDefs.ThreadViewPost):
            # Add current post with its depth
            self.posts.append((thread_node.post, depth))

            # Process replies if they exist
            if thread_node.replies:
                for reply in thread_node.replies:
                    self._flatten(reply, depth + 1)
        elif isinstance(thread_node, models.AppBskyFeedDefs.NotFoundPost):
            # Skip not found posts
            pass
        elif isinstance(thread_node, models.AppBskyFeedDefs.BlockedPost):
            # Skip blocked posts
            pass

    def print(self, format='', output=None, delimiter=' '):
        """
        Print thread in specified format.

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
        """Print thread to stdout."""
        from ssky.post_data_list import PostDataList

        # For short and id formats, add "| " prefix to replies
        if format in ('', 'id'):
            for idx, (post, depth) in enumerate(self.posts):
                post_list = PostDataList()
                post_list.append(post)

                # Capture the output
                import io
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                post_list.print(format=format, delimiter=delimiter)
                output = sys.stdout.getvalue()
                sys.stdout = old_stdout

                # Add prefix for replies (depth > 0)
                if depth > 0:
                    lines = output.rstrip('\n').split('\n')
                    for line in lines:
                        print("| " + line)
                else:
                    print(output.rstrip('\n'))

                # Add separator between posts within thread (long/text format only)
                if idx < len(self.posts) - 1 and format in ('long', 'text'):
                    print("|")
        else:
            # For long and text formats, print posts with "|" separator
            for idx, (post, depth) in enumerate(self.posts):
                post_list = PostDataList()
                post_list.append(post)
                post_list.print(format=format, delimiter=delimiter)

                # Add separator between posts within thread
                if idx < len(self.posts) - 1:
                    print("|")

    def _print_to_files(self, format, output_dir, delimiter):
        """
        Print thread to files.

        Args:
            format: Output format
            output_dir: Output directory path
            delimiter: Delimiter for short format
        """
        from ssky.post_data_list import PostDataList
        import io

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Get root post (first post in thread)
        if self.posts:
            root_post, _ = self.posts[0]

            # Generate filename from root post using same logic as PostDataList
            iso_datetime_str = root_post.record.created_at
            if iso_datetime_str is None:
                iso_datetime_str = "0000-00-00T00:00:00.000Z"
            import re
            datetime_components = re.split(r'T|Z|-|:|\+|\.', iso_datetime_str)
            formatted_datetime_str = ''.join(datetime_components[:6])
            filename = f"{root_post.author.handle}.{formatted_datetime_str}.txt"
            filepath = os.path.join(output_dir, filename)

            # Capture the formatted output by temporarily redirecting stdout
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            # Use the same logic as _print_to_stdout to preserve thread structure
            if format in ('', 'id'):
                for idx, (post, depth) in enumerate(self.posts):
                    post_list = PostDataList()
                    post_list.append(post)

                    # Capture the output
                    temp_stdout = sys.stdout
                    sys.stdout = io.StringIO()
                    post_list.print(format=format, delimiter=delimiter)
                    output = sys.stdout.getvalue()
                    sys.stdout = temp_stdout

                    # Add prefix for replies (depth > 0)
                    if depth > 0:
                        lines = output.rstrip('\n').split('\n')
                        for line in lines:
                            print("| " + line)
                    else:
                        print(output.rstrip('\n'))

                    # Add separator between posts within thread (long/text format only)
                    if idx < len(self.posts) - 1 and format in ('long', 'text'):
                        print("|")
            else:
                # For long and text formats, print posts with "|" separator
                for idx, (post, depth) in enumerate(self.posts):
                    post_list = PostDataList()
                    post_list.append(post)
                    post_list.print(format=format, delimiter=delimiter)

                    # Add separator between posts within thread
                    if idx < len(self.posts) - 1:
                        print("|")

            # Get the captured output and restore stdout
            content = sys.stdout.getvalue()
            sys.stdout = old_stdout

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
