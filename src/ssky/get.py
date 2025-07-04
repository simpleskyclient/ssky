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

def get(param=None, limit=25, **kwargs) -> PostDataList:
    try:
        current_session = ssky_client()
        if current_session is None:
            raise SessionError()
        
        if param is None:
            # Get timeline
            return get_timeline(current_session, limit=limit)
        elif param.startswith('at://'):
            # AT URI - single post or post with CID
            if is_joined_uri_cid(param):
                uri, cid = disjoin_uri_cid(param)
            else:
                uri = param
                cid = None
            return get_posts(current_session, uri, cid)
        elif param.startswith('did:'):
            # DID - get author feed
            return get_author_feed(current_session, param, limit=limit)
        else:
            # Handle or other identifier - expand and get author feed
            actor = expand_actor(param)
            if not actor:
                raise InvalidActorError()
            return get_author_feed(current_session, actor, limit=limit)
        
    except atproto_client.exceptions.AtProtocolError as e:
        raise AtProtocolSskyError(e) from e