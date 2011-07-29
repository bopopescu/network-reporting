""" For increased speed, we can keep a dictionary in memory. """
  

import sys
_cache = {}

def set(key, value):
    _cache[key] = value
    
def get(key):
    return _cache.get(key)          
    
    
# def space_used():              
#     """ This will only work in python 2.6+ """
#     return sys.getsizeof(_cache)        