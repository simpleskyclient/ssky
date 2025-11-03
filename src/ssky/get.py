import atproto_client
from ssky.ssky_session import expand_actor, ssky_client
from ssky.post_data_list import PostDataList
from ssky.thread_data import ThreadData
from ssky.thread_data_list import ThreadDataList
from ssky.result import (
    AtProtocolSskyError,
    SessionError,
    InvalidActorError,
    InvalidOptionCombinationError
)
from ssky.util import disjoin_uri_cid, is_joined_uri_cid

def get_posts(client, uri, cid) -> None:
    res = client.get_posts([uri])
    post_data_list = PostDataList()
    for post in res.posts:
        if post.uri == uri and (cid is None or post.cid == cid):
            post_data_list.append(post)
    return post_data_list

def get_author_feed(client, user, limit=100) -> None:
    res = client.get_author_feed(user, limit=limit)
    post_data_list = PostDataList()
    for feed_post in res.feed:
        post_data_list.append(feed_post.post)
    return post_data_list

def get_timeline(client, limit=100) -> None:
    res = client.get_timeline(limit=limit)
    post_data_list = PostDataList()
    for feed_post in res.feed:
        post_data_list.append(feed_post.post)
    return post_data_list

def get(target=None, limit=100, thread=False, thread_depth=10, thread_parent_height=0, format='', **kwargs):
    try:
        current_session = ssky_client()
        if current_session is None:
            raise SessionError()

        # Check for invalid option combination
        if thread and format in ('json', 'simple_json'):
            raise InvalidOptionCombinationError("--thread cannot be used with --json or --simple-json")

        # First, retrieve posts normally
        if target is None:
            # Get timeline
            post_data_list = get_timeline(current_session, limit=limit)
        elif target.startswith('at://'):
            # AT URI - single post or post with CID
            if is_joined_uri_cid(target):
                uri, cid = disjoin_uri_cid(target)
            else:
                uri = target
                cid = None
            post_data_list = get_posts(current_session, uri, cid)
        elif target.startswith('did:'):
            # DID - get author feed
            post_data_list = get_author_feed(current_session, target, limit=limit)
        else:
            # Handle or other identifier - expand and get author feed
            actor = expand_actor(target)
            if not actor:
                raise InvalidActorError()
            post_data_list = get_author_feed(current_session, actor, limit=limit)

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

            # Reverse to show newest first (matching result order)
            thread_data_list.threads.reverse()

            return thread_data_list
        else:
            return post_data_list

    except atproto_client.exceptions.AtProtocolError as e:
        raise AtProtocolSskyError(e) from e