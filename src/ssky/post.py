import re
import sys
from atproto import IdResolver, models
import atproto_client
from bs4 import BeautifulSoup
import requests
from ssky.ssky_session import ssky_client
from ssky.post_data_list import PostDataList
from ssky.result import (
    DryRunResult, 
    AtProtocolSskyError,
    SessionError, 
    NotFoundError, 
    TooManyImagesError
)
from ssky.util import disjoin_uri_cid, is_joined_uri_cid
from time import sleep
import logging
import atproto_client.exceptions

# Configure logger for post module
logger = logging.getLogger(__name__)

def get_card(links, warnings=None):
    if warnings is None:
        warnings = []
        
    headers = { 'Cache-Control': 'no-cache', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36' }
        
    cards = []
    for link in links.values():
        uri = link['uri']

        res = None
        try:
            res = requests.get(uri, headers=headers)
        except Exception as e:
            error_message = str(e)
            warnings.append(f'Failed to fetch card: {error_message}')
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
                warnings.append(f'HTTP error fetching card: {error}')
                continue

        if not 'Content-Type' in res.headers:
            warnings.append('No Content-Type header in card response')
            continue

        content_type_fragments = res.headers['Content-Type'].split(';')

        mime_type = content_type_fragments[0].strip().lower()
        if mime_type != 'text/html':
            warnings.append(f'Unexpected mime type: {mime_type}')
            continue

        if len(content_type_fragments) >= 2:
            charset = content_type_fragments[1].strip().lower()
            if not charset.startswith('charset='):
                warnings.append('Warning: get_card: No charset; assume utf-8')
                charset = 'utf-8'
            else:
                charset = charset[8:]
                if charset != 'utf-8':
                    warnings.append(f'Unexpected charset: {charset}')
                    continue
        else:
            warnings.append('Warning: get_card: No charset; assume utf-8')
            charset = 'utf-8'

        if len(res.content) == 0:
            warnings.append('Empty content in card response')
            continue

        # Import BeautifulSoup here to avoid import error if not installed
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            warnings.append('BeautifulSoup not available for card parsing')
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

        cards.append({
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uri': uri
        })

    return cards

def byte_len(text):
    return len(text.encode('UTF-8'))

def shorten_url(url):
    """
    Shorten URL according to the specification:
    - Remove 'https://' scheme
    - Keep authority (domain) as-is
    - For path:
      - If no directory: keep path as-is
      - If 1 directory level: keep first directory, shorten filename
        - Filename ≤3 chars: keep as-is
        - Filename >3 chars: truncate to first 3 chars + "..."
      - If 2+ directory levels: keep first directory, show 2nd directory + "..."
        - 2nd directory ≤3 chars: keep as-is + "..."
        - 2nd directory >3 chars: truncate to first 3 chars + "..."

    Examples:
    - https://example.com/path -> example.com/path
    - https://example.com/dir/file.html -> example.com/dir/fil...
    - https://example.com/dir/abc -> example.com/dir/abc
    - https://example.com/dir/subdir/file -> example.com/dir/sub...
    - https://example.com/directory/a/b/c -> example.com/directory/a...
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)

    # Get authority (netloc in urllib.parse)
    authority = parsed.netloc

    # Get path
    path = parsed.path

    # If no path or just '/', return authority only
    if not path or path == '/':
        return authority

    # Split path into components (remove empty strings)
    path_parts = [p for p in path.split('/') if p]

    # If no path components, return authority with path
    if not path_parts:
        return authority + path

    # If only one component (no directory)
    if len(path_parts) == 1:
        # No directory, just filename - keep as-is
        return authority + path

    # If exactly 2 components (1 directory + 1 filename)
    if len(path_parts) == 2:
        # First directory as-is, shorten filename
        first_dir = path_parts[0]
        filename = path_parts[1]

        if len(filename) <= 3:
            return authority + '/' + first_dir + '/' + filename
        else:
            return authority + '/' + first_dir + '/' + filename[:3] + '...'

    # If 3+ components (1 directory + subdirectories + filename)
    # Keep first directory, show 2nd directory with "..." to indicate continuation
    first_dir = path_parts[0]
    second_dir = path_parts[1]

    if len(second_dir) <= 3:
        # Short directory name, but add "..." to show there's more
        return authority + '/' + first_dir + '/' + second_dir + '...'
    else:
        # Long directory name, truncate and add "..."
        return authority + '/' + first_dir + '/' + second_dir[:3] + '...'

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

def get_thumbnail(uri, warnings=None):
    headers = { 'Cache-Control': 'no-cache', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36' }
    
    if warnings is None:
        warnings = []

    res = None
    try:
        res = requests.get(uri, headers=headers)
    except Exception as e:
        error_message = str(e)
        warnings.append(f'Failed to fetch thumbnail: {error_message}')
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
            warnings.append(f'HTTP error fetching thumbnail: {error}')
            return None

    if not 'Content-Type' in res.headers:
        warnings.append('No Content-Type header in thumbnail response')
        return None

    content_type_fragments = res.headers['Content-Type'].split(';')
    mime_type = content_type_fragments[0].strip().lower()
    if mime_type != 'image/jpeg' and mime_type != 'image/png' and mime_type != 'image/gif':
        warnings.append(f'Unexpected mime type for thumbnail: {mime_type}')
        return None

    return res.content

def load_images(image_paths):
    images = []
    for path in image_paths:
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

def post(message=None, image=None, dry=False, reply_to=None, quote=None, **kwargs):
    warnings = []  # Collect warnings during processing

    try:
        current_session = ssky_client()
        if current_session is None:
            raise SessionError()

        # Process message and extract facets
        if message:
            # First extract all facets from original message
            original_tags_dict = get_tags(message)
            original_links_dict = get_links(message)
            original_mentions_dict = get_mentions(message)

            # Replace URLs with shortened versions in the message text
            # Process in reverse order to avoid index shifting
            modified_message = message
            if original_links_dict:
                # Sort links by start position in reverse order
                sorted_links = sorted(original_links_dict.items(),
                                    key=lambda x: x[1]['start'], reverse=True)

                # Replace URLs in message text (reverse order avoids index issues)
                for key, link_data in sorted_links:
                    original_url = link_data['uri']
                    shortened_url = shorten_url(original_url)

                    start = link_data['start']
                    end = link_data['end']
                    modified_message = (modified_message[:start] +
                                      shortened_url +
                                      modified_message[end:])

                # Now re-extract facets from modified message to get correct positions
                tags_dict = get_tags(modified_message)
                mentions_dict = get_mentions(modified_message)

                # For links, we need to find shortened URLs but keep original URIs
                links_dict = {}
                for key, link_data in original_links_dict.items():
                    shortened_url = shorten_url(link_data['uri'])
                    # Find this shortened URL in the modified message
                    pattern = re.escape(shortened_url)
                    for match in re.finditer(pattern, modified_message):
                        match_key = f'{match.start():05d}'
                        # Avoid duplicate entries
                        if match_key not in links_dict:
                            links_dict[match_key] = {
                                'byte_start': byte_len(modified_message[:match.start()]),
                                'byte_end': byte_len(modified_message[:match.end()]),
                                'start': match.start(),
                                'end': match.end(),
                                'uri': link_data['uri']  # Keep original full URL
                            }
                            break

                # Update message to use modified version
                message = modified_message
            else:
                # No links to process
                tags_dict = original_tags_dict
                links_dict = original_links_dict
                mentions_dict = original_mentions_dict

            # Extract tag names only
            tags = [item['name'] for item in tags_dict.values()]
            # Extract link URIs only
            links = [item['uri'] for item in links_dict.values()]
            # Extract mention handles only
            mentions = [item['handle'] for item in mentions_dict.values()]

            # Get card info for links
            card = None
            if links_dict:
                cards = get_card(links_dict, warnings)
                if cards:
                    card = cards[0]  # Use the first card for now
        else:
            tags_dict = {}
            links_dict = {}
            mentions_dict = {}
            tags = []
            links = []
            mentions = []
            card = None
        
        # Handle dry run
        if dry:
            # Build preview data
            images_list = []
            
            if image:
                images_list = image if isinstance(image, list) else [image]
                if len(images_list) > 4:
                    raise TooManyImagesError()
            
            return DryRunResult(
                message=message or "",
                tags=tags,
                links=links,
                mentions=mentions,
                images=images_list,
                card=card,
                reply_to=reply_to,
                quote=quote
            )
        
        # Validate inputs
        if image and isinstance(image, list):
            if len(image) > 4:
                raise TooManyImagesError()
        
        # Handle reply_to
        reply_ref = None
        if reply_to:
            post_to_reply_to = get_post(reply_to)
            if post_to_reply_to is None:
                raise NotFoundError("Reply target")
            reply_ref = models.app.bsky.feed.post.ReplyRef(
                parent=models.create_strong_ref(post_to_reply_to),
                root=get_root_strong_ref(post_to_reply_to)
            )
        
        # Build facets for atproto
        facets = []
        
        # Add link facets
        for link_data in links_dict.values():
            facet = models.AppBskyRichtextFacet.Main(
                features=[models.AppBskyRichtextFacet.Link(uri=link_data['uri'])],
                index=models.AppBskyRichtextFacet.ByteSlice(
                    byte_start=link_data['byte_start'],
                    byte_end=link_data['byte_end']
                )
            )
            facets.append(facet)
        
        # Add tag facets
        for tag_data in tags_dict.values():
            facet = models.AppBskyRichtextFacet.Main(
                features=[models.AppBskyRichtextFacet.Tag(tag=tag_data['name'][1:])],  # Remove # prefix
                index=models.AppBskyRichtextFacet.ByteSlice(
                    byte_start=tag_data['byte_start'],
                    byte_end=tag_data['byte_end']
                )
            )
            facets.append(facet)
        
        # Add mention facets
        for mention_data in mentions_dict.values():
            if 'did' in mention_data and mention_data['did']:
                facet = models.AppBskyRichtextFacet.Main(
                    features=[models.AppBskyRichtextFacet.Mention(did=mention_data['did'])],
                    index=models.AppBskyRichtextFacet.ByteSlice(
                        byte_start=mention_data['byte_start'],
                        byte_end=mention_data['byte_end']
                    )
                )
                facets.append(facet)
        
        # Handle quote
        if quote:
            source = get_post(quote)
            if source is None:
                raise NotFoundError("Quote source")
            embed_record = models.AppBskyEmbedRecord.Main(
                record = models.ComAtprotoRepoStrongRef.Main(
                    uri = source.uri,
                    cid = source.cid
                )
            )
            result = current_session.send_post(text=message or "", facets=facets, embed=embed_record, reply_to=reply_ref)
        elif image:
            # Handle images with send_images method
            images = load_images(image if isinstance(image, list) else [image])
            result = current_session.send_images(
                text=message or "",
                facets=facets,
                images=images,
                reply_to=reply_ref
            )
        else:
            # Handle text-only post with send_post method
            result = current_session.send_post(
                text=message or "",
                facets=facets,
                reply_to=reply_ref
            )
        
        # Wait for post to be available and return it
        post = get_post(result.uri)
        while post is None:
            warnings.append('Waiting for post to become available')
            sleep(1)
            post = get_post(result.uri)
        
        # Create PostDataList and add warnings
        post_list = PostDataList().append(post)
        for warning in warnings:
            post_list.add_warning(warning)
        
        return post_list
        
    except atproto_client.exceptions.AtProtocolError as e:
        raise AtProtocolSskyError(e) from e