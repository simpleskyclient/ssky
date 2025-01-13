import os
import sys
from time import sleep
from ssky.delete import delete
from ssky.post import post
from ssky.post_data_list import PostDataList
from ssky.util import join_uri_cid
from tests.common import setup, teardown

def test_post_quote_reply_delete():
    setup()
    print('Dry post...', file=sys.stderr)
    dry_result = post(message=os.environ.get('SSKY_TEST_POST_TEXT'), image=[os.environ.get('SSKY_TEST_POST_IMAGE')], dry=True)
    print('Post...', file=sys.stderr)
    post_result = post(message=os.environ.get('SSKY_TEST_POST_TEXT'), image=[os.environ.get('SSKY_TEST_POST_IMAGE')])
    source_uri_cid = join_uri_cid(post_result[0].uri, post_result[0].cid)
    sleep(5)
    print('Quote...', file=sys.stderr)
    quote_result = post(message=os.environ.get('SSKY_TEST_POST_QUOTE_TEXT'), quote=source_uri_cid)
    sleep(5)
    print('Reply...', file=sys.stderr)
    reply_result = post(message=os.environ.get('SSKY_TEST_POST_REPLY_TEXT'), reply=source_uri_cid)
    sleep(5)
    print('Delete reply...', file=sys.stderr)
    delete_reply_result = delete(reply_result[0].uri)
    print('Delete quote...', file=sys.stderr)
    delete_quote_result = delete(quote_result[0].uri)
    print('Delete post...', file=sys.stderr)
    delete_post_result = delete(post_result[0].uri)

    teardown()
    assert type(dry_result) is list and type(post_result) is PostDataList and type(quote_result) is PostDataList and type(reply_result) is PostDataList and type(delete_reply_result) is str and type(delete_quote_result) is str and type(delete_post_result) is str