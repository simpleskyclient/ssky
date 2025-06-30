import sys
from atproto import models
import atproto_client
from ssky.profile_list import ProfileList
from ssky.ssky_session import ssky_client
from ssky.util import should_use_json_format, create_error_response, get_http_status_from_exception, ErrorResult

def user(q, limit=100, **kwargs) -> ProfileList:
    try:
        client = ssky_client()
        if client is None:
            error_result = ErrorResult("No valid session available", 401)
            if should_use_json_format(**kwargs):
                print(error_result.to_json())
            else:
                print(str(error_result), file=sys.stderr)
            return error_result
        res = client.app.bsky.actor.search_actors(
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
        http_code = get_http_status_from_exception(e)
        if 'response' in dir(e) and e.response is not None and hasattr(e.response, 'content') and hasattr(e.response.content, 'message'):
            message = e.response.content.message
        elif str(e) is not None and len(str(e)) > 0:
            message = str(e)
        else:
            message = e.__class__.__name__
        
        error_result = ErrorResult(message, http_code)
        if should_use_json_format(**kwargs):
            print(error_result.to_json())
        else:
            print(str(error_result), file=sys.stderr)
        return error_result