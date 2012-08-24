import unicodedata

def normalize(s):
    """
    Safely/sanely ransforms a string from unicode to ascii.
    """
    return unicodedata.normalize('NFKD', unicode(s)).encode('ascii','ignore')

def sanitize(s, replace_with=None):
    """
    Replace control chars, unicode chars, and whitespace with '?'.
    """
    if not replace_with: replace_with = '?'
    return ''.join(c if (32 < ord(c) < 127) else replace_with for c in s)