from datetime import datetime
import os
import re
from atproto_client import models
from ssky.util import join_uri_cid, summarize, create_success_response

class PostDataList:

    class Item:
        post: models.AppBskyFeedDefs.PostView = None

        def __init__(self, post: models.AppBskyFeedDefs.PostView, profile: models.AppBskyActorDefs.ProfileViewDetailed = None, uri_cid: str = None) -> None:
            self.post = post
            if profile:
                self.post.author = models.AppBskyActorDefs.ProfileViewBasic(
                    associated=profile.associated,
                    avatar=profile.avatar,
                    created_at=profile.created_at,
                    did=profile.did,
                    display_name=profile.display_name,
                    handle=profile.handle,
                    labels=profile.labels,
                    viewer=profile.viewer
                )
            if uri_cid:
                self.post.uri, self.post.cid = uri_cid.split('::')

        def id(self) -> str:
            return join_uri_cid(self.post.uri, self.post.cid)

        def _process_urls_from_facets(self, text: str) -> str:
            """
            facets情報を使用してテキスト内の切り詰められたURLを完全なURLに復元する
            URLのみを処理し、メンションやタグは処理しない
            """
            if not text or not hasattr(self.post.record, 'facets') or not self.post.record.facets:
                return text
            
            # テキストをバイト配列として処理
            text_bytes = text.encode('utf-8')
            
            # facetsを逆順でソートして後ろから処理（インデックスがずれないように）
            sorted_facets = sorted(self.post.record.facets, 
                                  key=lambda f: f.index.byte_start, reverse=True)
            
            for facet in sorted_facets:
                for feature in facet.features:
                    # URLリンクのみを処理
                    if hasattr(feature, 'uri'):  # Link facet
                        start = facet.index.byte_start
                        end = facet.index.byte_end
                        
                        # バイト単位で切り詰められた部分を完全なURLに置換
                        replacement_bytes = feature.uri.encode('utf-8')
                        text_bytes = (text_bytes[:start] + 
                                    replacement_bytes + 
                                    text_bytes[end:])
            
            # バイト配列を文字列に戻す
            return text_bytes.decode('utf-8')

        def text_only(self) -> str:
            text = self.post.record.text if self.post.record.text else ''
            return self._process_urls_from_facets(text)

        def short(self, delimiter: str = None) -> str:
            if delimiter is None:
                delimiter = PostDataList.get_default_delimiter()
            uri_cid = self.id()
            author_did = self.post.author.did
            author_handle = self.post.author.handle
            display_name_summary = summarize(self.post.author.display_name)
            text_summary = summarize(self.post.record.text, length_max=40)
            return delimiter.join([uri_cid, author_did, author_handle, display_name_summary, text_summary])

        def long(self) -> str:
            text_summary = self.post.record.text if self.post.record.text else ''
            text_summary = self._process_urls_from_facets(text_summary)
            return '\n'.join(
                filter(
                    lambda x: x is not None,
                    [
                        f'Author-DID: {self.post.author.did}',
                        f'Author-Display-Name: {self.post.author.display_name}',
                        f'Author-Handle: {self.post.author.handle}',
                        f'Created-At: {self.post.record.created_at}',
                        f'Record-CID: {self.post.cid}',
                        f'Record-URI: {self.post.uri}',
                        f'Repost-URI: {self.post.viewer.repost}' if self.post.viewer and self.post.viewer.repost else None,
                        f'',
                        text_summary
                    ]
                )
            )

        def json(self) -> str:
            return models.utils.get_model_as_json(self.post)

        def get_simple_data(self) -> dict:
            """Return simplified post data as dict (without wrapping in success response)"""
            text = self.post.record.text if self.post.record.text else ""
            processed_text = self._process_urls_from_facets(text)
            return {
                "uri": self.post.uri,
                "cid": self.post.cid,
                "author": {
                    "did": self.post.author.did,
                    "handle": self.post.author.handle,
                    "display_name": self.post.author.display_name,
                    "avatar": self.post.author.avatar
                },
                "text": processed_text,
                "created_at": self.post.record.created_at,
                "reply_count": self.post.reply_count if hasattr(self.post, 'reply_count') else 0,
                "repost_count": self.post.repost_count if hasattr(self.post, 'repost_count') else 0,
                "like_count": self.post.like_count if hasattr(self.post, 'like_count') else 0,
                "indexed_at": self.post.indexed_at if hasattr(self.post, 'indexed_at') else None
            }

        def simple_json(self) -> str:
            """Return simplified post data wrapped in success response"""
            return create_success_response(data=self.get_simple_data())

        def printable(self, format: str, delimiter: str = None) -> str:
            if format == 'id':
                return self.id()
            elif format == 'long':
                return self.long()
            elif format == 'text':
                return self.text_only()
            elif format == 'json':
                return self.json()
            elif format == 'simple_json':
                return self.simple_json()
            else:
                return self.short(delimiter=delimiter)

        def get_filename(self) -> str:
            iso_datetime_str = self.post.record.created_at
            if iso_datetime_str is None:
                iso_datetime_str = "0000-00-00T00:00:00.000Z"
            datetime_components = re.split(r'T|Z|-|:|\+|\.', iso_datetime_str) 
            formatted_datetime_str = ''.join(datetime_components[:6])
            filename = f"{self.post.author.handle}.{formatted_datetime_str}.txt"
            return filename

    default_delimiter = ' '

    @classmethod
    def set_default_delimiter(cls, delimiter: str) -> None:
        cls.default_delimiter = delimiter

    @classmethod
    def get_default_delimiter(cls) -> str:
        return cls.default_delimiter

    def __init__(self, default_delimiter: str = None) -> None:
        self.items = []
        if default_delimiter is not None:
            self.default_delimiter = default_delimiter

    def __str__(self) -> str:
        return str(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> 'PostDataList':
        self.index = 0
        return self

    def __next__(self) -> models.AppBskyFeedDefs.PostView:
        if self.index >= len(self.items):
            raise StopIteration
        item = self.items[self.index]
        self.index += 1
        return item.post

    def __getitem__(self, index: int) -> models.AppBskyFeedDefs.PostView:
        return self.items[index].post

    def append(self, post: models.AppBskyFeedDefs.PostView, profile: models.AppBskyActorDefs.ProfileViewDetailed = None, uri_cid: str = None) -> 'PostDataList':
        item = self.Item(post, profile=profile, uri_cid=uri_cid)
        if item.id() not in [i.id() for i in self.items]:
            self.items.append(item)
        return self

    def print(self, format: str, output: str = None, delimiter: str = None) -> None:
        if output:
            # Output each item to separate files
            for item in self.items:
                filename = item.get_filename()
                path = os.path.join(output, filename)
                with open(path, 'w') as f:
                    f.write(item.printable(format, delimiter=delimiter))
                    f.write('\n')
        else:
            # Console output
            if format == 'simple_json':
                # Output all items as a single JSON response
                posts_data = []
                for item in self.items:
                    posts_data.append(item.get_simple_data())
                print(create_success_response(data=posts_data))
            else:
                # Output each item individually
                for i, item in enumerate(self.items):
                    # Add separator before second and subsequent items for long format
                    if format == 'long' and i > 0:
                        print('----------------')
                    print(item.printable(format, delimiter=delimiter))