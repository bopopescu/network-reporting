import unicodedata
import logging

def normalize(s):
    """
    Safely/sanely ransforms a string from unicode to ascii.
    """
    return unicodedata.normalize('NFKD', unicode(s)).encode('ascii','ignore')

def sanitize(s, replace_with=None):
    """
    Replace control chars, unicode chars, and whitespace with '?'.
    More aggressive than `normalize`
    """
    if not replace_with: replace_with = '?'
    return ''.join(c if (32 < ord(c) < 127) else replace_with for c in s)

def sanitize_string_for_export(string):
    """
    Looks like some filenames are rejected by Chrome, which is a
    Chrome bug.  This function strips characters in filenames that
    cause this situation to arise.
    
    More info: https://code.djangoproject.com/ticket/17620
    """
    logging.info('sanitize_string_for_export')
    logging.info('Filename would have been: ' + string)
    
    bad_characters = (
        ' ',
        '\t',
        '\n',
        '\r',
        "'",
        '"',
        '-',
        ',',
        '.'
    )
    
    for character in bad_characters:        
        string = string.replace(character, '')
        
    logging.info('Sanitized to: ' + string)
    
    return string