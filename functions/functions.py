from config import Config
from cryptography.fernet import Fernet
import json
import datetime
import time
import pytz

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

def get_unix_today_midnight():
    current_datetime = datetime.datetime.now()
    one_day = datetime.timedelta(days=1)
    # yesterday_datetime = current_datetime - one_day
    current_datetime = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(current_datetime.timestamp())

def get_meeting_end_time(utc_datetime_str, minutes_to_add, local_timezone_str):
    utc_datetime = datetime.datetime.strptime(utc_datetime_str, "%Y-%m-%dT%H:%M:%SZ")
    local_timezone = pytz.timezone(local_timezone_str)
    local_datetime = utc_datetime.replace(tzinfo=pytz.utc).astimezone(local_timezone)
    result_local_datetime = local_datetime + datetime.timedelta(minutes=minutes_to_add)
    return int(result_local_datetime.timestamp())

def convert_zoom_time_format(utc_datetime_str, local_timezone_str):
    utc_datetime = datetime.datetime.strptime(utc_datetime_str, "%Y-%m-%dT%H:%M:%SZ")
    local_timezone = pytz.timezone(local_timezone_str)
    local_datetime = utc_datetime.replace(tzinfo=pytz.utc).astimezone(local_timezone)
    return int(local_datetime.timestamp())