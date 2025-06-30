import sys
import atproto_client
from ssky.profile_list import ProfileList
from ssky.ssky_session import expand_actor, ssky_client
from ssky.util import should_use_json_format, create_error_response, get_http_status_from_exception, ErrorResult

def follow(name, **kwargs) -> str:
    try:
        client = ssky_client()
        if client is None:
            error_result = ErrorResult("No valid session available", 401)
            if should_use_json_format(**kwargs):
                print(error_result.to_json())
            else:
                print(str(error_result), file=sys.stderr)
            return error_result
        actor = expand_actor(name)
        if actor is None:
            error_result = ErrorResult("Invalid actor identifier", 400)
            if should_use_json_format(**kwargs):
                print(error_result.to_json())
            else:
                print(str(error_result), file=sys.stderr)
            return error_result
        profile = client.get_profile(actor)
        client.follow(profile.did)
        return ProfileList().append(profile.did)
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