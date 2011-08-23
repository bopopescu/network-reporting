from iad import iad
from text import text         
from html import html
from html_full import html_full
from admob_native import admob_native
from millennial_native import millennial_native
from string import Template
from custom_native import custom_native            

TEMPLATES = {                    
        "clear"     : Template(""),
        "html"      : html,
        "html_full" : html_full,
        "iAd"       : iad,              
        "text"      : text,       
        "admob_native" : admob_native,
        "custom_native" : custom_native,
        "millennial_native" : millennial_native
        }    
        
