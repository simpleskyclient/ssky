import atproto_client
from ssky.profile_list import ProfileList
from ssky.ssky_session import expand_actor, ssky_client
from ssky.result import (
    AtProtocolSskyError,
    SessionError, 
    InvalidActorError, 
    NotFoundError
)

def profile(actor=None, **kwargs) -> ProfileList:
    try:
        current_session = ssky_client()
        if current_session is None:
            raise SessionError()
        
        if actor is None:
            actor = current_session.me.handle
        else:
            actor = expand_actor(actor)
            if actor is None:
                raise InvalidActorError()
        
        profile_data = current_session.get_profile(actor)
        if profile_data is None:
            raise NotFoundError("Profile")
        
        return ProfileList().append(profile_data.did)
    except atproto_client.exceptions.AtProtocolError as e:
        raise AtProtocolSskyError(e) from e