import sys
from atproto import models
import atproto_client
from ssky.profile_list import ProfileList
from ssky.ssky_session import ssky_client

def user(q, limit=100, **kwargs) -> ProfileList:
    try:
        res = ssky_client().app.bsky.actor.search_actors(
            models.AppBskyActorSearchActors.Params(
                limit=limit,
                q=q
            )
        )

        actor_list = ProfileList()
        for actor in res.actors:
            actor_list.append(actor.did)
        return actor_list
    except atproto_client.exceptions.AtProtocolError as e:
        if 'response' in dir(e) and e.response is not None:
            print(f'{e.response.status_code} {e.response.content.message}', file=sys.stderr)
        elif str(e) is not None and len(str(e)) > 0:
            print(f'{str(e)}', file=sys.stderr)
        else:
            print(f'{e.__class__.__name__}', file=sys.stderr)
        return None