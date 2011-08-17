from adsense import adsense
from iad import iad
from text import text
from text_icon import text_icon
from image import image
from html import html
from html_full import html_full
from admob_native import admob_native
from millennial_native import millennial_native
from string import Template
from custom_native import custom_native            

TEMPLATES = {
        "adsense"   : adsense,
        "clear"     : Template(""),
        "html"      : html,
        "html_full" : html_full,
        "iAd"       : iad,
        "image"     : image,
        "text"      : text,
        "text_icon" : text_icon,
        "admob_native" : admob_native,
        "custom_native" : custom_native,
        "millennial_native" : millennial_native
        }    
        
