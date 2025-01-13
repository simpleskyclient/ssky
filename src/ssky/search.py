import re
import sys
from atproto import models
import atproto_client
from ssky.ssky_session import expand_actor, ssky_client
from ssky.post_data_list import PostDataList

def search(q, author=None, since=None, until=None, limit=100, **kwargs) -> PostDataList:
    if since:
        if re.match(r'^\d{14}$', since):
            since = f'{since[:4]}-{since[4:6]}-{since[6:8]}T{since[8:10]}:{since[10:12]}:{since[10:12]}Z'
        elif re.match(r'^\d{8}$', since):
            since = f'{since[:4]}-{since[4:6]}-{since[6:8]}T00:00:00Z'
        else:
            since = since
    else:
        since = None

    if until:
        if re.match(r'^\d{14}$', until):
            until = f'{until[:4]}-{until[4:6]}-{until[6:8]}T{until[8:10]}:{until[10:12]}:{until[10:12]}Z'
        elif re.match(r'^\d{8}$', until):
            until = f'{until[:4]}-{until[4:6]}-{until[6:8]}T23:59:59Z'
        else:
            until = until
    else:
        until = None

    try:
        res = ssky_client().app.bsky.feed.search_posts(
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
        return post_data_list
    except atproto_client.exceptions.AtProtocolError as e:
        if 'response' in dir(e) and e.response is not None:
            print(f'{e.response.status_code} {e.response.content.message}', file=sys.stderr)
        elif str(e) is not None and len(str(e)) > 0:
            print(f'{str(e)}', file=sys.stderr)
        else:
            print(f'{e.__class__.__name__}', file=sys.stderr)
        return None