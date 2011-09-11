from common.utils import simplejson

# TODO: Make explicit set of properties
class HeaderContext(object):
    def __init__(self):
        self._dict = {}
        
    def add_header(self, key, value):
        self._dict[key] = value  
        
        
    def to_json(self):
        return simplejson.dumps(self._dict) 
    
    @classmethod
    def from_json(cls, json):
        new_context = HeaderContext()
        new_context._dict = simplejson.loads(json)
        return new_context
                                
        
    def __repr__(self):
        return str(self._dict) 
        
        
    def __eq__(self, other):
        return self._dict == other._dict  
        
    def __iter__(self):
        return self._dict.__iter__()
        
    def next(self):
        return self._dict.next()
        
    def items(self):
        return self._dict.items() 