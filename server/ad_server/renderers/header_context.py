from common.utils import simplejson


class HeaderContext(object):
    """Encapsulation of the header properties to be used when rendering a creative"""
    
    
#     mapping of actual header names to the property names used in this class.
#     allows users to deal with simple names and then automatically translate them
#     into appropriate headers
#     see items() for example of how this translation works
    attr_mappings = {"X-Refreshtime" : "refresh_time",
                     "X-Interceptlinks" : "intercept_links",
                     "X-Clickthrough" : "click_through",
                     "X-Imptracker" : "imp_tracker",
                     "X-Orientation" : "orientation",
                     "X-Launchpage" : "launch_page",
                     "X-Scrollable" : "scrollable",
                     "X-Adtype" : "ad_type",
                     "X-Fulladtype" : "full_ad_type",
                     "X-Failurl" : "fail_url",
                     "X-Nativeparams" : "native_params",
                     "X-Width" : "width",
                     "X-Height" : "height",
                     "X-Networktype" : "network_type",
                     "X-Creativeid" : "creative_id",
                     "X-Format" : "format",
                     "X-Backgroundcolor" : "background_color",
                     "X-Customselector" : "custom_selector",
                     }
    
    def __init__(self,
                 refresh_time=None,
                 intercept_links=None,
                 click_through=None,
                 imp_tracker=None,
                 orientation=None,
                 launch_page=None,
                 scrollable=None,
                 ad_type=None,
                 full_ad_type=None,
                 fail_url=None,
                 native_params=None,
                 width=None,
                 height=None,
                 network_type=None,
                 creative_id=None,
                 format=None,
                 background_color=None,
                 custom_selector=None):
        self.refresh_time = refresh_time
        self.intercept_links = intercept_links
        self.click_through = click_through
        self.imp_tracker = imp_tracker
        self.orientation = orientation
        self.launch_page = launch_page
        self.scrollable = scrollable
        self.ad_type = ad_type
        self.full_ad_type = full_ad_type
        self.fail_url = fail_url
        self.native_params = native_params
        self.width = width
        self.height = height
        self.network_type = network_type
        self.creative_id = creative_id
        self.format = format
        self.background_color = background_color
        self.custom_selector = custom_selector
        
        
    def items(self):
        """
        Generator that yields all Header Key / value pairs that are currently
        set in the HeaderContext. Translates from attribute name to 
        header name using the attr_mappings dictionary
        """
        for k, v in self.attr_mappings.items():
            attr = getattr(self, v)
            if attr:
                yield (k, str(attr))
    
    @property
    def _dict(self):
        """
        Returns a dict representation of the HeaderContext
        """
        new_dict = {}
        for k, v in self.items():
            new_dict[k] = v
        return new_dict

    def to_json(self):
        return simplejson.dumps(self._dict) 
        
    @classmethod
    def from_json(cls, json):
        new_context = HeaderContext()
        new_dict = simplejson.loads(json)
        for k, v in cls.attr_mappings.items():
            if new_dict.has_key(k):
                setattr(new_context, v, str(new_dict[k]))
        return new_context
        
    
    def __eq__(self, other):
        return self._dict == other._dict

    def __repr__(self):
        return self._dict.__repr__()
        
