import sys
import atproto_client
from ssky.ssky_session import SskySession

def login(handle=None, password=None, **kwargs) -> list:
    try:
        session = SskySession(handle=handle, password=password)
        session.persist()
        handle = session.profile().handle
        did = session.profile().did
        return [did, handle]
    except atproto_client.exceptions.AtProtocolError as e:
        if 'response' in dir(e) and e.response is not None:
            print(f'{e.response.status_code} {e.response.content.message}', file=sys.stderr)
        elif str(e) is not None and len(str(e)) > 0:
            print(f'{str(e)}', file=sys.stderr)
        else:
            print(f'{e.__class__.__name__}', file=sys.stderr)
        return None