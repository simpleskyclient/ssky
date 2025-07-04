import atproto_client
from ssky.profile_list import ProfileList
from ssky.ssky_session import expand_actor, ssky_client, ssky_profile
from ssky.result import (
    AtProtocolSskyError,
    SessionError,
    InvalidActorError,
    NotFoundError,
    OperationFailedError
)

def unfollow(actor, **kwargs) -> ProfileList:
    try:
        current_session = ssky_client()
        if current_session is None:
            raise SessionError()
        
        profile = ssky_profile()
        if profile is None:
            raise SessionError()
        
        if not actor or actor.strip() == "":
            raise InvalidActorError()
        
        actor = expand_actor(actor)
        if actor is None:
            raise InvalidActorError()
        
        res = current_session.get_follows(profile.did)
        for follow in res.follows:
            if follow.did == actor or follow.handle == actor:
                if follow.viewer.following:
                    status = current_session.unfollow(follow.viewer.following)
                    if status is False:
                        raise OperationFailedError("Failed to unfollow")
                    else:
                        return ProfileList().append(follow.did)
        
        raise NotFoundError(f"You are not following {actor}")
    except atproto_client.exceptions.AtProtocolError as e:
        raise AtProtocolSskyError(e) from e