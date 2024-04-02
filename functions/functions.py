from config import Config
from cryptography.fernet import Fernet
import json
import datetime
import time

def decrypt_credentials(encrypted_data):
    cipher_suite = Fernet(Config.ENCRYPTION_KEY)
    decrypted_data = cipher_suite.decrypt(encrypted_data.encode()).decode()
    return json.loads(decrypted_data)

def encrypt_credentials(credentials_dict, key):
    plain_text = json.dumps(credentials_dict)
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(plain_text.encode()).decode()

def get_unix_time(ntime=None):
	if not ntime:
		ntime = datetime.datetime.now()
	unix_time = time.mktime(ntime.timetuple())
	return int(unix_time)

def get_unix_yesterday():
    current_datetime = datetime.datetime.now()
    one_day = datetime.timedelta(days=1)
    yesterday_datetime = current_datetime - one_day
    yesterday_midnight = yesterday_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(yesterday_midnight.timestamp())