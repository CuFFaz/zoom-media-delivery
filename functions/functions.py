from config import Config
from cryptography.fernet import Fernet
import json

def decrypt_credentials(encrypted_data):
    cipher_suite = Fernet(Config.ENCRYPTION_KEY)
    decrypted_data = cipher_suite.decrypt(encrypted_data.encode()).decode()
    return json.loads(decrypted_data)

def encrypt_credentials(credentials_dict, key):
    plain_text = json.dumps(credentials_dict)
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(plain_text.encode()).decode()
