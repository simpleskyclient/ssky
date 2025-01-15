import datetime
import re
import sys
from atproto import models
import atproto_client
from ssky.ssky_session import expand_actor, ssky_client
from ssky.post_data_list import PostDataList

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

def search(q='*', author=None, since=None, until=None, limit=100, **kwargs) -> PostDataList:
    since = expand_datetime(since)
    until = expand_datetime(until)

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