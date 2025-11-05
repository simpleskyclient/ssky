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

            # Reverse to show newest first (matching result order)
            thread_data_list.threads.reverse()

            return thread_data_list
        else:
            return post_data_list

    except atproto_client.exceptions.AtProtocolError as e:
        raise AtProtocolSskyError(e) from e