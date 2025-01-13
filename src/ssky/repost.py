import sys
import atproto_client
from ssky.post_data_list import PostDataList
from ssky.ssky_session import ssky_client
from ssky.util import disjoin_uri_cid, is_joined_uri_cid, join_uri_cid

def repost(post, **kwargs) -> str:
    if is_joined_uri_cid(post):
        source_uri, source_cid = disjoin_uri_cid(post)
    else:
        source_uri = post
        source_cid = None

    try:
        post_data_list = PostDataList()
        sources = ssky_client().get_posts([source_uri])
        for source_post in sources.posts:
            if source_post.uri == source_uri and (source_cid is None or source_post.cid == source_cid):
                post_data_list.append(source_post)
                source_cid = source_post.cid
                break

        ssky_client().repost(source_uri, source_cid)
        return post_data_list
    except atproto_client.exceptions.AtProtocolError as e:
        if 'response' in dir(e) and e.response is not None:
            print(f'{e.response.status_code} {e.response.content.message}', file=sys.stderr)
        elif str(e) is not None and len(str(e)) > 0:
            print(f'{str(e)}', file=sys.stderr)
        else:
            print(f'{e.__class__.__name__}', file=sys.stderr)
        return None