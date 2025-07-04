import atproto_client
from ssky.profile_list import ProfileList
from ssky.ssky_session import expand_actor, ssky_client
from ssky.result import (
    AtProtocolSskyError,
    SessionError, 
    InvalidActorError
)

def follow(actor, **kwargs) -> ProfileList:
    try:
        current_session = ssky_client()
        if current_session is None:
            raise SessionError()
        
        if not actor or actor.strip() == "":
            raise InvalidActorError()
        
        actor = expand_actor(actor)
        if actor is None:
            raise InvalidActorError()
        
        profile = current_session.get_profile(actor)
        current_session.follow(profile.did)
        return ProfileList().append(profile.did)
    except atproto_client.exceptions.AtProtocolError as e:
        raise AtProtocolSskyError(e) from e