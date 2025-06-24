import os
import sys
from time import sleep
from ssky.delete import delete
from ssky.post import post
from ssky.post_data_list import PostDataList
from ssky.util import join_uri_cid, ErrorResult
from tests.common import setup, teardown

def test_post_quote_reply_delete():
    setup()
    print('Dry post...', file=sys.stderr)
    dry_result = post(message=os.environ.get('SSKY_TEST_POST_TEXT'), image=[os.environ.get('SSKY_TEST_POST_IMAGE')], dry=True)
    
    print('Post...', file=sys.stderr)
    post_result = post(message=os.environ.get('SSKY_TEST_POST_TEXT'), image=[os.environ.get('SSKY_TEST_POST_IMAGE')])
    
    # Check if post failed due to rate limiting or other errors
    if isinstance(post_result, ErrorResult):
        print(f'Post failed: {post_result.message} (HTTP {post_result.http_code})', file=sys.stderr)
        teardown()
        # For rate limiting errors, we skip the test instead of failing
        if post_result.http_code == 429:
            import pytest
            pytest.skip("Rate limit exceeded - skipping test")
        else:
            assert False, f"Post failed: {post_result.message}"
    
    source_uri_cid = join_uri_cid(post_result[0].uri, post_result[0].cid)
    sleep(5)
    
    print('Quote...', file=sys.stderr)
    quote_result = post(message=os.environ.get('SSKY_TEST_POST_QUOTE_TEXT'), quote=source_uri_cid)
    if isinstance(quote_result, ErrorResult):
        print(f'Quote failed: {quote_result.message} (HTTP {quote_result.http_code})', file=sys.stderr)
        teardown()
        if quote_result.http_code == 429:
            import pytest
            pytest.skip("Rate limit exceeded - skipping test")
        else:
            assert False, f"Quote failed: {quote_result.message}"
    
    sleep(5)
    print('Reply...', file=sys.stderr)
    reply_result = post(message=os.environ.get('SSKY_TEST_POST_REPLY_TEXT'), reply_to=source_uri_cid)
    if isinstance(reply_result, ErrorResult):
        print(f'Reply failed: {reply_result.message} (HTTP {reply_result.http_code})', file=sys.stderr)
        teardown()
        if reply_result.http_code == 429:
            import pytest
            pytest.skip("Rate limit exceeded - skipping test")
        else:
            assert False, f"Reply failed: {reply_result.message}"
    
    sleep(5)
    print('Delete reply...', file=sys.stderr)
    delete_reply_result = delete(reply_result[0].uri)
    print('Delete quote...', file=sys.stderr)
    delete_quote_result = delete(quote_result[0].uri)
    print('Delete post...', file=sys.stderr)
    delete_post_result = delete(post_result[0].uri)

    teardown()
    assert type(dry_result) is list and type(post_result) is PostDataList and type(quote_result) is PostDataList and type(reply_result) is PostDataList and type(delete_reply_result) is str and type(delete_quote_result) is str and type(delete_post_result) is str