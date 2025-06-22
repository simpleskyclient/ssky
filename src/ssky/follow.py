import sys
import atproto_client
from ssky.profile_list import ProfileList
from ssky.ssky_session import expand_actor, ssky_client
from ssky.util import should_use_json_format, create_error_response, get_http_status_from_exception

def follow(name, **kwargs) -> str:
    try:
        client = ssky_client()
        actor = expand_actor(name)
        profile = client.get_profile(actor)
        client.follow(profile.did)
        return ProfileList().append(profile.did)
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