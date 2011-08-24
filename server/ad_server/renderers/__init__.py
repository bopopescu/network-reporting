from iad import iad
from text import text         
from html import html
from admob_native import admob_native            
from string import Template

TEMPLATES = {                    
        "clear"     : Template(""),
        "html"      : html,
        "iAd"       : iad,              
        "text"      : text,       
        "admob_native" : admob_native,
        }    
        
