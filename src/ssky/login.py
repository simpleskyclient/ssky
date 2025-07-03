from typing import Union
import atproto_client
from ssky.profile_list import ProfileList
from ssky.ssky_session import SskySession
from ssky.util import get_http_status_from_exception, ErrorResult

def login(credentials=None, **kwargs) -> Union[ErrorResult, ProfileList]:
    handle = None
    password = None
    
    # Parse credentials if provided
    if credentials is not None:
        if not credentials.strip():  # Empty or whitespace-only string
            return ErrorResult("Empty credentials provided", 400)
        if ':' in credentials:
            handle, password = credentials.split(':', 1)
        else:
            # Invalid format - no colon separator
            return ErrorResult("Invalid credential format - expected 'handle:password'", 400)
    
    try:
        session = SskySession(handle=handle, password=password)
        session.persist()
        
        # Check if profile is available
        profile = session.profile()
        if profile is None or not hasattr(profile, 'did') or profile.did is None:
            return ErrorResult("Profile not available after login", 500)
        
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
        
    except Exception as e:
        # Catch any other unexpected exceptions
        return ErrorResult(f"Unexpected error during login: {str(e)}", 500)
