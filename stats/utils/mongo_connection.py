from mongoengine import connect

CONNECTED = False

def ensure_connection():
    global CONNECTED
    if not CONNECTED:
        try:
            connect("marketplace")
            CONNECTED = True
        except:
            pas
