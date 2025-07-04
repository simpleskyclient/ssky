import atproto_client
from ssky.profile_list import ProfileList
from ssky.ssky_session import SskySession
from .result import (
    AtProtocolSskyError,
    EmptyCredentialsError,
    InvalidCredentialFormatError,
    ProfileUnavailableAfterLoginError
)

def login(credentials=None, **kwargs) -> ProfileList:
    try:
        handle = None
        password = None
        
        if credentials is not None:
            if not credentials.strip():  # Empty or whitespace-only string
                raise EmptyCredentialsError()
            if ':' in credentials:
                handle, password = credentials.split(':', 1)
            else:
                # Invalid format - no colon separator
                raise InvalidCredentialFormatError()
        
        session = SskySession(handle=handle, password=password)

        profile = session.profile()
        if profile is None or not hasattr(profile, 'did') or profile.did is None:
            raise ProfileUnavailableAfterLoginError()
        
        return ProfileList().append(profile.did)
    except atproto_client.exceptions.AtProtocolError as e:
        raise AtProtocolSskyError(e) from e
