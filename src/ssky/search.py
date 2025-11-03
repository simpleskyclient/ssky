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
            seen_uris = set()  # URIs already included in other threads

            # Process in reverse order (oldest first) to prioritize parent posts
            for item in reversed(post_data_list.items):
                # Skip if this post is already part of another thread
                if item.post.uri in seen_uris:
                    continue

                # Get thread for each post
                thread_response = current_session.get_post_thread(
                    item.post.uri,
                    depth=thread_depth,
                    parent_height=thread_parent_height
                )
                thread_data = ThreadData(thread_response)

                # Mark all URIs in this thread as seen
                for post, depth in thread_data.posts:
                    seen_uris.add(post.uri)

                thread_data_list.append(thread_data)

            # Reverse to show newest first (matching search result order)
            thread_data_list.threads.reverse()

            return thread_data_list
        else:
            return post_data_list

    except atproto_client.exceptions.AtProtocolError as e:
        raise AtProtocolSskyError(e) from e