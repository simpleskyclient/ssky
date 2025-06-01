import sys
import atproto_client
from ssky.profile_list import ProfileList
from ssky.ssky_session import SskySession

def login(credentials=None, **kwargs) -> ProfileList:
    handle = None
    password = None
    
    # Parse credentials if provided
    if credentials is not None and ':' in credentials:
        handle, password = credentials.split(':', 1)
    
    try:
        session = SskySession(handle=handle, password=password)
        session.persist()
        return ProfileList().append(session.profile().did)
    except atproto_client.exceptions.AtProtocolError as e:
        if 'response' in dir(e) and e.response is not None:
            print(f'{e.response.status_code} {e.response.content.message}', file=sys.stderr)
        elif str(e) is not None and len(str(e)) > 0:
            print(f'{str(e)}', file=sys.stderr)
        else:
            print(f'{e.__class__.__name__}', file=sys.stderr)
        return None