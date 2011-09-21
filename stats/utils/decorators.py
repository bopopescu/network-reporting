from utils.mongo_connection import is_connected, ensure_connection
from inspect import getargspec
from functools import wraps

def web_dec(f):
    """ Unpackages get values that are names in kwargs. """
    @wraps(f)
    def new_f(self, *args, **kwargs):

        # (all_args, varargs, keywords, defaults) = getargspec(f)
        resp_tuple = getargspec(f)
    
        all_args = resp_tuple[0]
        
        # For each of the view_args, try to get them from get
               
        for arg in all_args:
            request_arg = self.get_argument(arg, default=None)
            if request_arg:
                kwargs[arg] = request_arg
        
        return f(self, *args, **kwargs)

    return new_f

def requires_mongo(orig_fun):
    if not is_connected():
        def new_fun(*args, **kwargs):
            ensure_connection()
            orig_fun(*args, **kwargs)
        return new_fun
    else:
        return fun
