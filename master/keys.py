import os.path
from securesystemslib.interface import generate_and_write_ed25519_keypair, import_ed25519_privatekey_from_file, import_ed25519_publickey_from_file
from securesystemslib.keys import verify_signature, create_signature

PASSWORD = "123"
KEY_NAME = "ed25519_key"

def init_keys():
    if not os.path.isfile(KEY_NAME):
        generate_and_write_ed25519_keypair(KEY_NAME, password=PASSWORD)

def get_private_key():
    init_keys()
    return import_ed25519_privatekey_from_file(KEY_NAME, password=PASSWORD)

def get_public_key():
    init_keys()
    return import_ed25519_publickey_from_file(KEY_NAME+'.pub')

def sign_data(data):
    return create_signature(get_private_key(), data)

def verify_data(signature, data):
    return verify_signature(get_private_key(), signature, data)
