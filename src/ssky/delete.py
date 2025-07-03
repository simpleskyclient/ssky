import atproto_client
from ssky.ssky_session import ssky_client
from ssky.util import disjoin_uri_cid, is_joined_uri_cid, get_http_status_from_exception, ErrorResult, SuccessResult
from typing import Union

def delete(post, **kwargs) -> Union[ErrorResult, SuccessResult]:
    if is_joined_uri_cid(post):
        uri, _ = disjoin_uri_cid(post)
    else:
        uri = post

    try:
        client = ssky_client()
        if client is None:
            return ErrorResult("No valid session available", 401)
        
        status = client.delete_post(uri)
        if status is False:
            return ErrorResult("Failed to delete", 500)
        
        return SuccessResult(data=uri, message=f"Post deleted: {uri}")
        
    except atproto_client.exceptions.LoginRequiredError as e:
        return ErrorResult(str(e), 401)
        
    except atproto_client.exceptions.AtProtocolError as e:
        http_code = get_http_status_from_exception(e)
        if 'response' in dir(e) and e.response is not None and hasattr(e.response, 'content') and hasattr(e.response.content, 'message'):
            message = e.response.content.message
        elif str(e) is not None and len(str(e)) > 0:
            message = str(e)
        else:
            message = e.__class__.__name__
        
        return ErrorResult(message, http_code)