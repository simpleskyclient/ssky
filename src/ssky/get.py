import atproto_client
from ssky.ssky_session import expand_actor, ssky_client
from ssky.post_data_list import PostDataList
from ssky.result import (
    AtProtocolSskyError,
    SessionError,
    InvalidActorError
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

def get(target=None, limit=100, **kwargs) -> PostDataList:
    try:
        current_session = ssky_client()
        if current_session is None:
            raise SessionError()
        
        if target is None:
            # Get timeline
            return get_timeline(current_session, limit=limit)
        elif target.startswith('at://'):
            # AT URI - single post or post with CID
            if is_joined_uri_cid(target):
                uri, cid = disjoin_uri_cid(target)
            else:
                uri = target
                cid = None
            return get_posts(current_session, uri, cid)
        elif target.startswith('did:'):
            # DID - get author feed
            return get_author_feed(current_session, target, limit=limit)
        else:
            # Handle or other identifier - expand and get author feed
            actor = expand_actor(target)
            if not actor:
                raise InvalidActorError()
            return get_author_feed(current_session, actor, limit=limit)
        
    except atproto_client.exceptions.AtProtocolError as e:
        raise AtProtocolSskyError(e) from e