import sys
import atproto_client
from ssky.ssky_session import ssky_client
from ssky.util import disjoin_uri_cid, is_joined_uri_cid, should_use_json_format, create_error_response, get_http_status_from_exception, ErrorResult

def delete(post, **kwargs) -> str:
    if is_joined_uri_cid(post):
        uri, _ = disjoin_uri_cid(post)
    else:
        uri = post

    try:
        client = ssky_client()
        if client is None:
            error_result = ErrorResult("No valid session available", 401)
            if should_use_json_format(**kwargs):
                print(error_result.to_json())
            else:
                print(str(error_result), file=sys.stderr)
            return error_result
        
        status = client.delete_post(uri)
        if status is False:
            error_result = ErrorResult("Failed to delete", 500)
            if should_use_json_format(**kwargs):
                print(error_result.to_json())
            else:
                print(str(error_result), file=sys.stderr)
            return error_result
        return uri
    except atproto_client.exceptions.LoginRequiredError as e:
        error_result = ErrorResult(str(e), 401)
        if should_use_json_format(**kwargs):
            print(error_result.to_json())
        else:
            print(str(error_result), file=sys.stderr)
        return error_result
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