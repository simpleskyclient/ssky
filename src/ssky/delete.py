import sys
import atproto_client
from ssky.ssky_session import ssky_client
from ssky.util import disjoin_uri_cid, is_joined_uri_cid, should_use_json_format, create_error_response, get_http_status_from_exception

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
        if should_use_json_format(**kwargs):
            http_code = get_http_status_from_exception(e)
            if 'response' in dir(e) and e.response is not None and hasattr(e.response, 'content') and hasattr(e.response.content, 'message'):
                message = e.response.content.message
            elif str(e) is not None and len(str(e)) > 0:
                message = str(e)
            else:
                message = e.__class__.__name__
            error_response = create_error_response(message=message, http_code=http_code)
            print(error_response)
            return None
        else:
            if 'response' in dir(e) and e.response is not None:
                print(f'{e.response.status_code} {e.response.content.message}', file=sys.stderr)
            elif str(e) is not None and len(str(e)) > 0:
                print(f'{str(e)}', file=sys.stderr)
            else:
                print(f'{e.__class__.__name__}', file=sys.stderr)
            return None