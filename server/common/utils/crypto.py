from Crypto.Cipher import AES
import base64
import os
BLOCK_SIZE = 32

PADDING = '{'

# one-liner to sufficiently pad the text to be encrypted
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING

# one-liners to encrypt/encode and decrypt/decode a string
# encrypt with AES, encode with base64
EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)

# generate a random secret key
SECRET_KEY = '\x86\xb6;\x8eK!\xd7+\x1b\xad\x94\x89\xb69v\xd3n\xe0~i\xa1\xb8\xfc\xd4\xcc\xd9Bv\xa0\x04\x17\xe5'
# create a cipher object using the random secret

def get_cipher(iv):
    return AES.new(SECRET_KEY, AES.MODE_CBC, iv)
