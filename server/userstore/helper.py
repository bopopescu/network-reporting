def get_key_name(key):
    if type(key) == type(list()):
        return 'k:%s'%('|'.join(key))
    else:
        return 'k:%s'%key

def get_required_param(param, kwargs):
    if param not in kwargs:
        raise NameError('%s is required'%param)
    else:
        return kwargs[param]


