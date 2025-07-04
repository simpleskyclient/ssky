import atproto_client
from ssky.ssky_session import ssky_client
from ssky.result import (
    AtProtocolSskyError,
    SuccessResult, 
    SessionError, 
    OperationFailedError
)
from ssky.util import disjoin_uri_cid, is_joined_uri_cid

def delete(target, **kwargs) -> SuccessResult:
    try:
        current_session = ssky_client()
        if current_session is None:
            raise SessionError()
        
        if is_joined_uri_cid(target):
            uri, cid = disjoin_uri_cid(target)
        else:
            uri = target
            cid = None
        
        result = current_session.delete_post(uri)
        if not result:
            raise OperationFailedError("delete post")
        
        return SuccessResult(data={"deleted": uri}, message="Post deleted successfully")
    except atproto_client.exceptions.AtProtocolError as e:
        raise AtProtocolSskyError(e) from e