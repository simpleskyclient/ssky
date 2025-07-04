from atproto import models
import atproto_client
from ssky.profile_list import ProfileList
from ssky.ssky_session import ssky_client
from ssky.result import (
    AtProtocolSskyError,
    SessionError
)

def user(query, limit=25, **kwargs) -> ProfileList:
    try:
        current_session = ssky_client()
        if current_session is None:
            raise SessionError()
        
        response = current_session.app.bsky.actor.search_actors(
            models.AppBskyActorSearchActors.Params(
                limit=limit,
                q=query
            )
        )
        
        result = ProfileList()
        if response.actors:
            for actor in response.actors:
                result.append(actor.did)
        
        return result
    except atproto_client.exceptions.AtProtocolError as e:
        raise AtProtocolSskyError(e) from e