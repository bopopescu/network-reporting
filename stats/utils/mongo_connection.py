from mongoengine import connect

CONNECTED = False

def ensure_connection(db="marketplace"):
    global CONNECTED
    if not CONNECTED:
        try:
            connect(db)
            CONNECTED = True
        except:
            pass

def is_connected():
    return CONNECTED
