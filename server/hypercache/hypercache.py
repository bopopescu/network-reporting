""" For increased speed, we can keep a dictionary in memory.
    To prevent overloading the appengine memory limit, we keep a limited 
    number of elements in the cache. We purge things in LRU order.

"""  

from lru_cache import LRUCache



MAX_ELTS = 500 # We limit the max number of elts in the cache    
_cache = LRUCache(MAX_ELTS)
                    


def set(key, value):
    _cache.put(key, value)
    
def get(key):
    return _cache.get(key)          
    
    
# def space_used():              
#     """ This will only work in python 2.6+ """
#     return sys.getsizeof(_cache)
