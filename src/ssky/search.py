import datetime
import re
from atproto import models
import atproto_client
from ssky.ssky_session import expand_actor, ssky_client
from ssky.post_data_list import PostDataList
from ssky.thread_data import ThreadData
from ssky.thread_data_list import ThreadDataList
from ssky.result import (
    AtProtocolSskyError,
    SessionError,
    InvalidOptionCombinationError
)

def expand_datetime(dt: str) -> str:
    if dt:
        if dt == 'today':
            ymd = datetime.datetime.now().strftime('%Y%m%d')
            return f'{ymd[:4]}-{ymd[4:6]}-{ymd[6:8]}T00:00:00Z'
        elif dt == 'yesterday':
            ymd = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y%m%d')
            return f'{ymd[:4]}-{ymd[4:6]}-{ymd[6:8]}T00:00:00Z'
        elif re.match(r'^\d{14}$', dt):
            return f'{dt[:4]}-{dt[4:6]}-{dt[6:8]}T{dt[8:10]}:{dt[10:12]}:{dt[10:12]}Z'
        elif re.match(r'^\d{8}$', dt):
            return f'{dt[:4]}-{dt[4:6]}-{dt[6:8]}T00:00:00Z'
        else:
            return dt
    else:
        return None

def search(q='*', author=None, since=None, until=None, limit=100, thread=False, thread_depth=10, thread_parent_height=0, format='', **kwargs):
    since = expand_datetime(since)
    until = expand_datetime(until)

    try:
        current_session = ssky_client()
        if current_session is None:
            raise SessionError()

        # Check for invalid option combination
        if thread and format in ('json', 'simple_json'):
            raise InvalidOptionCombinationError("--thread cannot be used with --json or --simple-json")

        res = current_session.app.bsky.feed.search_posts(
            models.AppBskyFeedSearchPosts.Params(
                author=expand_actor(author),
                limit=limit,
                q=q,
                since=since,
                until=until
            )
        )

        post_data_list = PostDataList()
        if res.posts and len(res.posts) > 0:
            for post in res.posts:
                post_data_list.append(post)

        # If --thread is specified, expand each post into threads
        if thread:
            thread_data_list = ThreadDataList()

            # Group posts by their root thread URI
            thread_groups = {}  # {root_uri: [posts]}
            root_order = []  # Track order of root URIs for maintaining result order

            for item in post_data_list.items:
                # Determine the root URI of this post's thread
                if hasattr(item.post.record, 'reply') and item.post.record.reply:
                    root_uri = item.post.record.reply.root.uri
                else:
                    root_uri = item.post.uri  # This post is the root

                # Add to group and track order
                if root_uri not in thread_groups:
                    thread_groups[root_uri] = []
                    root_order.append(root_uri)
                thread_groups[root_uri].append(item.post)

            # Fetch each thread once using its root URI
            for root_uri in reversed(root_order):  # Process oldest first
                thread_response = current_session.get_post_thread(
                    root_uri,
                    depth=thread_depth,
                    parent_height=thread_parent_height
                )
                thread_data = ThreadData(thread_response)
                thread_data_list.append(thread_data)

            # Reverse to show newest first (matching search result order)
            thread_data_list.threads.reverse()

            return thread_data_list
        else:
            return post_data_list

    except atproto_client.exceptions.AtProtocolError as e:
        raise AtProtocolSskyError(e) from e