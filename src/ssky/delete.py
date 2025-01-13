import sys
import atproto_client
from ssky.ssky_session import ssky_client
from ssky.util import disjoin_uri_cid, is_joined_uri_cid

def delete(post, **kwargs) -> str:
    if is_joined_uri_cid(post):
        uri, _ = disjoin_uri_cid(post)
    else:
        uri = post

    try:
        status = ssky_client().delete_post(uri)
        if status is False:
            print('Failed to delete', file=sys.stderr)
            return None
        return uri
    except atproto_client.exceptions.AtProtocolError as e:
        if 'response' in dir(e) and e.response is not None:
            print(f'{e.response.status_code} {e.response.content.message}', file=sys.stderr)
        elif str(e) is not None and len(str(e)) > 0:
            print(f'{str(e)}', file=sys.stderr)
        else:
            print(f'{e.__class__.__name__}', file=sys.stderr)
        return None