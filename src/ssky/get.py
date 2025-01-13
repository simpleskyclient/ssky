import sys
import atproto_client
from ssky.ssky_session import expand_actor, ssky_client
from ssky.post_data_list import PostDataList
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
        client = ssky_client()
        if target is None:
            post_data_list = get_timeline(client, limit=limit)
        elif target.startswith('at://'):
            if is_joined_uri_cid(target):
                uri, cid = disjoin_uri_cid(target)
            else:
                uri = target
                cid = None
            post_data_list = get_posts(client, uri, cid)
        elif target.startswith('did:'):
            post_data_list = get_author_feed(client, target, limit=limit)
        else:
            actor = expand_actor(target)
            post_data_list = get_author_feed(client, actor, limit=limit)
        return post_data_list
    except atproto_client.exceptions.AtProtocolError as e:
        if 'response' in dir(e) and e.response is not None:
            print(f'{e.response.status_code} {e.response.content.message}', file=sys.stderr)
        elif str(e) is not None and len(str(e)) > 0:
            print(f'{str(e)}', file=sys.stderr)
        else:
            print(f'{e.__class__.__name__}', file=sys.stderr)
        return None