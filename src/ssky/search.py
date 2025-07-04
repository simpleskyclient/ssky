import datetime
import re
from atproto import models
import atproto_client
from ssky.ssky_session import expand_actor, ssky_client
from ssky.post_data_list import PostDataList
from ssky.result import (
    AtProtocolSskyError,
    SessionError
)

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

def search(query=None, author=None, since=None, until=None, limit=25, **kwargs) -> PostDataList:
    try:
        current_session = ssky_client()
        if current_session is None:
            raise SessionError()
        
        if author is not None:
            author = expand_actor(author)
        
        # Build search query
        search_query = query if query else ""
        if author:
            search_query += f" from:{author}"
        if since:
            if isinstance(since, str):
                if since.lower() == "today":
                    since = datetime.now().strftime("%Y-%m-%d")
                elif since.lower() == "yesterday":
                    since = (datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            search_query += f" since:{since}"
        if until:
            if isinstance(until, str):
                if until.lower() == "today":
                    until = datetime.now().strftime("%Y-%m-%d")
                elif until.lower() == "yesterday":
                    until = (datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            search_query += f" until:{until}"
        
        response = current_session.app.bsky.feed.search_posts(params={
            'q': search_query.strip(),
            'limit': limit
        })
        
        result = PostDataList()
        if response.posts:
            for post in response.posts:
                result.append(post)
        
        return result
    except atproto_client.exceptions.AtProtocolError as e:
        raise AtProtocolSskyError(e) from e