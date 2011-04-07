from adsense import adsense
from iad import iad
from text import text
from text_icon import text_icon
from image import image
from admob import admob
from html import html
from html_full import html_full
from string import Template

TEMPLATES = {
        "admob"     : admob,
        "adsense"   : adsense,
        "clear"     : Template(""),
        "html"      : html,
        "html_full" : html_full,
        "iAd"       : iad,
        "image"     : image,
        "text"      : text,
        "text_icon" : text_icon,
        }
