from utils.mongo_connection import is_connected, ensure_connection

def requires_mongo(orig_fun):
    if not is_connected():
        def new_fun(*args, **kwargs):
            ensure_connection()
            orig_fun(*args, **kwargs)
        return new_fun
    else:
        return fun
