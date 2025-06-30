import datetime
import re
import sys
from atproto import models
import atproto_client
from ssky.ssky_session import expand_actor, ssky_client
from ssky.post_data_list import PostDataList
from ssky.util import should_use_json_format, create_error_response, get_http_status_from_exception, ErrorResult

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
        client = ssky_client()
        if client is None:
            error_result = ErrorResult("No valid session available", 401)
            if should_use_json_format(**kwargs):
                print(error_result.to_json())
            else:
                print(str(error_result), file=sys.stderr)
            return error_result
        res = client.app.bsky.feed.search_posts(
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
        http_code = get_http_status_from_exception(e)
        if 'response' in dir(e) and e.response is not None and hasattr(e.response, 'content') and hasattr(e.response.content, 'message'):
            message = e.response.content.message
        elif str(e) is not None and len(str(e)) > 0:
            message = str(e)
        else:
            message = e.__class__.__name__
        
        error_result = ErrorResult(message, http_code)
        if should_use_json_format(**kwargs):
            print(error_result.to_json())
        else:
            print(str(error_result), file=sys.stderr)
        return error_result