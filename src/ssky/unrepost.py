import sys
import atproto_client
from ssky.post_data_list import PostDataList
from ssky.ssky_session import ssky_client
from ssky.util import disjoin_uri_cid, is_joined_uri_cid, should_use_json_format, create_error_response, get_http_status_from_exception, ErrorResult

def unrepost(post, **kwargs) -> PostDataList | ErrorResult:
    if is_joined_uri_cid(post):
        source_uri, source_cid = disjoin_uri_cid(post)
    else:
        source_uri = post
        source_cid = None

    try:
        client = ssky_client()
        if client is None:
            error_result = ErrorResult("No valid session available", 401)
            if should_use_json_format(**kwargs):
                print(error_result.to_json())
            else:
                print(str(error_result), file=sys.stderr)
            return error_result
        
        post_data_list = PostDataList()
        sources = client.get_posts([source_uri])
        repost_uri = None
        for source_post in sources.posts:
            if source_post.uri == source_uri and (source_cid is None or source_post.cid == source_cid):
                post_data_list.append(source_post)
                repost_uri = source_post.viewer.repost
                break

        if repost_uri is None:
            error_result = ErrorResult("Post not found", 404)
            if should_use_json_format(**kwargs):
                print(error_result.to_json())
            else:
                print(str(error_result), file=sys.stderr)
            return error_result

        status = client.unrepost(repost_uri)
        if status is False:
            error_result = ErrorResult("Failed to unrepost", 500)
            if should_use_json_format(**kwargs):
                print(error_result.to_json())
            else:
                print(str(error_result), file=sys.stderr)
            return error_result

        return post_data_list
    except atproto_client.exceptions.LoginRequiredError as e:
        error_result = ErrorResult(str(e), 401)
        if should_use_json_format(**kwargs):
            print(error_result.to_json())
        else:
            print(str(error_result), file=sys.stderr)
        return error_result
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