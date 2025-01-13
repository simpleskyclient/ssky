import re

def summarize(source, length_max=0):
    if source is None:
        return ''
    else:
        summary = re.sub(r'\s', '_', ''.join(list(map(lambda c: c if c > ' ' else ' ', source.rstrip()))))
        if length_max > 0 and len(summary) > length_max:
            summary = ''.join(summary[:length_max - 2]) + '..'
        return summary

def join_uri_cid(uri, cid) -> str:
    return '::'.join([uri, cid])

def disjoin_uri_cid(uri_cid) -> tuple:
    pair = uri_cid.split('::', 1)
    return pair[0], pair[1]

def is_joined_uri_cid(uri_cid) -> bool:
    return '::' in uri_cid