import atproto_client
from ssky.post_data_list import PostDataList
from ssky.ssky_session import ssky_client
from ssky.result import (
    AtProtocolSskyError,
    SessionError,
    InvalidUriError
)
from ssky.util import disjoin_uri_cid, is_joined_uri_cid

def repost(target, **kwargs) -> PostDataList:
    if is_joined_uri_cid(target):
        source_uri, source_cid = disjoin_uri_cid(target)
    else:
        source_uri = target
        source_cid = None

    try:
        current_session = ssky_client()
        if current_session is None:
            raise SessionError()
        
        if not target or target.strip() == "":
            raise InvalidUriError()
        
        post_data_list = PostDataList()
        sources = current_session.get_posts([source_uri])
        for source_post in sources.posts:
            if source_post.uri == source_uri and (source_cid is None or source_post.cid == source_cid):
                post_data_list.append(source_post)
                source_cid = source_post.cid
                break

        current_session.repost(source_uri, source_cid)
        return post_data_list
    except atproto_client.exceptions.AtProtocolError as e:
        raise AtProtocolSskyError(e) from e