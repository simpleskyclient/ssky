import atproto_client
from ssky.profile_list import ProfileList
from ssky.ssky_session import expand_actor, ssky_client
from ssky.util import get_http_status_from_exception, ErrorResult
from typing import Union

def profile(name, **kwargs) -> Union[ErrorResult, ProfileList]:
    try:
        client = ssky_client()
        if client is None:
            return ErrorResult("No valid session available", 401)
        
        actor = expand_actor(name)
        if actor is None:
            return ErrorResult("Invalid actor identifier", 400)
        
        profile = client.get_profile(actor)
        if profile is None:
            return ErrorResult("Profile not found", 404)
        
        return ProfileList().append(profile.did)
        
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