import re
import sys
from time import sleep
from atproto import IdResolver, models
import atproto_client
from bs4 import BeautifulSoup
import requests
from ssky.ssky_session import ssky_client
from ssky.post_data_list import PostDataList
from ssky.util import disjoin_uri_cid, is_joined_uri_cid, should_use_json_format, create_error_response, get_http_status_from_exception, ErrorResult

def get_card(links):
    title = None
    description = None

    headers = { 'Cache-Control': 'no-cache', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36' }

    for key in links:
        uri = links[key]['uri']

        res = None
        try:
            res = requests.get(uri, headers=headers)
        except Exception as e:
            error_message = str(e)
            print(f'{error_message}', file=sys.stderr)
            continue

        if res.status_code >= 400:
            if res.status_code == 403:
                headers_no_user_agent = { 'Cache-Control': 'no-cache' }

                res_no_user_agent = None
                try:
                    res_no_user_agent = requests.get(uri, headers=headers_no_user_agent)
                except Exception as e:
                    pass

                if res_no_user_agent is not None:
                    res = res_no_user_agent

            if res.status_code >= 400:
                error = ' '.join([str(res.status_code), res.text if res.text is not None else ''])
                print(f'{error} ', file=sys.stderr)
                continue

        if not 'Content-Type' in res.headers:
            print('No Content-Type', file=sys.stderr)
            continue

        content_type_fragments = res.headers['Content-Type'].split(';')

        mime_type = content_type_fragments[0].strip().lower()
        if mime_type != 'text/html':
            print(f'Unexpected mime type {mime_type}', file=sys.stderr)
            continue

        if len(content_type_fragments) < 2:
            print(f'Warning: get_card: No charset; assume utf-8', file=sys.stderr)
        else:
            charset = content_type_fragments[1].split('=')[1].strip().lower()
            if charset != 'utf-8':
                print(f'Unexpected charset {charset}', file=sys.stderr)
                continue

        if len(res.text) == 0:
            print('Empty content', file=sys.stderr)
            continue

        soup = BeautifulSoup(res.content, 'html.parser')

        title = 'No title'
        result = soup.find('title')
        if result is not None:
            title = result.text
        else:
            result = soup.find('meta', attrs={'property': 'og:title'})
            if result is not None:
                title = result.get('content')

        description = uri
        result = soup.find('meta', attrs={'name': 'description'})
        if result is not None:
            description = result.get('content')
        else:
            result = soup.find('meta', attrs={'property': 'og:description'})
            if result is not None:
                description = result.get('content')

        thumbnail = None
        result = soup.find('meta', attrs={'property': 'og:image'})
        if result is not None:
            thumbnail = result.get('content')
            if len(thumbnail) == 0:
                thumbnail = None

        return {
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uri': uri
        }

    return None

def byte_len(text):
    return len(text.encode('UTF-8'))

def search_items(text, pattern, property_name):
    matches = re.finditer(pattern, text)
    items = {}
    for m in matches:
        byte_start = byte_len(text[:m.start()])
        byte_end = byte_start + byte_len(m.group())
        items[f'{m.start():05d}'] = {
            'byte_start': byte_start,
            'byte_end': byte_end,
            'start': m.start(),
            'end': m.end(),
            property_name: m.group()
        }
    return items

def get_links(message):
    return search_items(message, r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+', 'uri')

def get_tags(message):
    return search_items(message, r'#\S+', 'name')

def get_mentions(message):
    mentions = search_items(message, r'@[\w.]+', 'handle')
    for key in mentions:
        name = mentions[key]['handle'][1:]
        resolver = IdResolver()
        did = resolver.handle.resolve(name)
        mentions[key]['did'] = did
    return mentions

def get_thumbnail(uri):
    headers = { 'Cache-Control': 'no-cache', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36' }

    res = None
    try:
        res = requests.get(uri, headers=headers)
    except Exception as e:
        error_message = str(e)
        print(f'{error_message}', file=sys.stderr)
        return None

    if res.status_code >= 400:
        if res.status_code == 403:
            headers_no_user_agent = { 'Cache-Control': 'no-cache' }

            res_no_user_agent = None
            try:
                res_no_user_agent = requests.get(uri, headers=headers_no_user_agent)
            except Exception as e:
                pass

            if res_no_user_agent is not None:
                res = res_no_user_agent

        if res.status_code >= 400:
            error = ' '.join([str(res.status_code), res.text if res.text is not None else ''])
            print(f'{error} ', file=sys.stderr)
            return None

    if not 'Content-Type' in res.headers:
        print('No Content-Type', file=sys.stderr)
        return None

    content_type_fragments = res.headers['Content-Type'].split(';')
    mime_type = content_type_fragments[0].strip().lower()
    if mime_type != 'image/jpeg' and mime_type != 'image/png' and mime_type != 'image/gif':
        print(f'Unexpected mime type {mime_type}', file=sys.stderr)
        return None

    return res.content

def load_images(paths):
    images = []
    for path in paths:
        with open(path, 'rb') as f:
            images.append(f.read())
    return images

def get_post(uri_cid):
    if is_joined_uri_cid(uri_cid):
        uri, cid = disjoin_uri_cid(uri_cid)
    else:
        uri = uri_cid
        cid = None
    retrieved_posts =ssky_client().get_posts([uri])
    posts = []
    for retrieved_post in retrieved_posts.posts:
        if retrieved_post.uri == uri and (cid is None or retrieved_post.cid == cid):
            posts.append(retrieved_post)

    if len(posts) == 0:
        return None

    return posts[0]

def get_root_strong_ref(post):
    slug = post.uri.split('/')[-1]
    did = post.author.did
    cid = post.cid
    retrieved_post = ssky_client().get_post(slug, profile_identify=did,cid=cid)
    if retrieved_post.value.reply is None:
        return models.create_strong_ref(post)
    else:
        return retrieved_post.value.reply.root

def post(message=None, dry=False, image=[], quote=None, reply_to=None, **kwargs) -> PostDataList:
    if message:
        message = message
    else:
        message = sys.stdin.read()

    message = message.strip()
    
    # Check client availability early (except for dry run)
    if not dry:
        try:
            client = ssky_client()
            if client is None:
                error_result = ErrorResult("No valid session available", 401)
                if should_use_json_format(**kwargs):
                    print(error_result.to_json())
                else:
                    print(str(error_result), file=sys.stderr)
                return error_result
        except atproto_client.exceptions.LoginRequiredError as e:
            error_result = ErrorResult(str(e), 401)
            if should_use_json_format(**kwargs):
                print(error_result.to_json())
            else:
                print(str(error_result), file=sys.stderr)
            return error_result

    tags = get_tags(message)
    links = get_links(message)
    mentions = get_mentions(message)

    card = None
    if len(image) == 0 and not quote:
        card = get_card(links)

    if dry:
        result = []
        result.append([message])
        for key in tags:
            result.append(['Tag', tags[key]['name']])
        for key in links:
            result.append(['Link', links[key]['uri']])
        for key in mentions:
            result.append(['Mention', mentions[key]['did'], mentions[key]['handle']])
        for img in image:
            result.append(['Image', img])
        if card is not None:
            result.append(['Card', card["uri"], card['title'], card['description'], card['thumbnail']])
        if reply_to:
            result.append(['Reply to', reply_to])
        return result

    facets = []
    for key in tags:
        facets.append(
            models.AppBskyRichtextFacet.Main(
                features=[models.AppBskyRichtextFacet.Tag(tag=tags[key]['name'][1:])],
                index=models.AppBskyRichtextFacet.ByteSlice(byte_start=tags[key]['byte_start'], byte_end=tags[key]['byte_end'])
            )
        )
    for key in links:
        facets.append(
            models.AppBskyRichtextFacet.Main(
                features=[models.AppBskyRichtextFacet.Link(uri=links[key]['uri'])],
                index=models.AppBskyRichtextFacet.ByteSlice(byte_start=links[key]['byte_start'], byte_end=links[key]['byte_end'])
            )
        )

    for key in mentions:
        facets.append(
            models.AppBskyRichtextFacet.Main(
                features=[models.AppBskyRichtextFacet.Mention(did=mentions[key]['did'])],
                index=models.AppBskyRichtextFacet.ByteSlice(byte_start=mentions[key]['byte_start'], byte_end=mentions[key]['byte_end'])
            )
        )

    try:
        reply_ref = None
        if reply_to:
            post_to_reply_to = get_post(reply_to)
            if post_to_reply_to is None:
                error_result = ErrorResult("Reply target is missing", 404)
                if should_use_json_format(**kwargs):
                    print(error_result.to_json())
                else:
                    print(str(error_result), file=sys.stderr)
                return error_result
            reply_ref = models.app.bsky.feed.post.ReplyRef(
                parent=models.create_strong_ref(post_to_reply_to),
                root=get_root_strong_ref(post_to_reply_to)
            )

        if card is not None:
            thumb_blob_ref = None
            if card['thumbnail'] is not None:
                image = get_thumbnail(card['thumbnail'])
                if image is not None:
                    res = ssky_client().upload_blob(image)
                    if res.blob is None:
                        error_result = ErrorResult("Failed to upload thumbnail", 500)
                        if should_use_json_format(**kwargs):
                            print(error_result.to_json())
                        else:
                            print(str(error_result), file=sys.stderr)
                        return error_result
                    thumb_blob_ref = res.blob

            embed_external = models.AppBskyEmbedExternal.Main(
                external = models.AppBskyEmbedExternal.External(
                    title = card['title'],
                    description = card['description'],
                    uri = card['uri'],
                    thumb = thumb_blob_ref
                )
            )
            res = ssky_client().send_post(text=message, facets=facets, embed=embed_external, reply_to=reply_ref)
        elif quote is not None:
            source = get_post(quote)
            if source is None:
                error_result = ErrorResult("Quote source is missing", 404)
                if should_use_json_format(**kwargs):
                    print(error_result.to_json())
                else:
                    print(str(error_result), file=sys.stderr)
                return error_result
            embed_record = models.AppBskyEmbedRecord.Main(
                record = models.ComAtprotoRepoStrongRef.Main(
                    uri = source.uri,
                    cid = source.cid
                )
            )
            res = ssky_client().send_post(text=message, facets=facets, embed=embed_record, reply_to=reply_ref)
        elif image is not None:
            if len(image) > 4:
                error_result = ErrorResult("Too many image files", 400)
                if should_use_json_format(**kwargs):
                    print(error_result.to_json())
                else:
                    print(str(error_result), file=sys.stderr)
                return error_result
            images = load_images(image)
            res = ssky_client().send_images(text=message, facets=facets, images=images, reply_to=reply_ref)
        else:
            res = ssky_client().send_post(text=message, facets=facets, reply_to=reply_ref)

        post = get_post(res.uri)
        while post is None:
            print('waiting', file=sys.stderr)
            sleep(1)
            post = get_post(res.uri)

        return PostDataList().append(post)
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