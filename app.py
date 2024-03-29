from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from config import DevelopmentConfig, ProductionConfig
from models.models import db, Sources, Recording, SchedulerLog, RemoteDatabases
from scheduler.scheduler import fetch_meetings_from_lms, fetch_recordings_from_source, \
                                push_recordings_to_dest, pull_recording_status_from_dest
from cryptography.fernet import Fernet
from config import Config

import atexit
import json

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
# app.config.from_object(ProductionConfig)

db.init_app(app)

with app.app_context():
    db.create_all()

# APScheduler setup
scheduler = BackgroundScheduler(daemon=True)
scheduler.start()

# job_defaults = {
#     'coalesce': False,
#     'max_instances': 1
# }
# scheduler.configure(job_defaults=job_defaults)

# scheduler.add_job(fetch_meetings_from_lms, 'interval', seconds=10)
# scheduler.add_job(fetch_recordings_from_source, 'interval', seconds=10)
# scheduler.add_job(push_recordings_to_dest, 'interval', seconds=10)
# scheduler.add_job(pull_recording_status_from_dest, 'interval', seconds=10)
atexit.register(lambda: scheduler.shutdown())

# Encryption key


def mandatory_keyval_empty_check(data, keys):
    for key in keys:
        if key not in data:
            return [False, key]
        elif data[key] == "":
            return [False, key]
    return [True, True]

def encrypt_credentials(credentials_dict, key):
    plain_text = json.dumps(credentials_dict)
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(plain_text.encode()).decode()

def decrypt_credentials(encrypted_data, key):
    cipher_suite = Fernet(key)
    decrypted_data = cipher_suite.decrypt(encrypted_data.encode()).decode()
    return json.loads(decrypted_data)

@app.route('/')
def index():

    credentials = RemoteDatabases.query.first()
    if credentials:
        decrypted_src = decrypt_credentials(credentials.src, Config.ENCRYPTION_KEY)
        decrypted_pwd = decrypt_credentials(credentials.pwd, Config.ENCRYPTION_KEY)

        print(decrypted_src)
        print(decrypted_pwd)
    return 'Running!'

@app.route('/add', methods=['POST'])
def store_credentials():
    data = request.json

    field_status = mandatory_keyval_empty_check(data, ["host", "uname", "pwd", "db_name"])
    if not field_status[0]:
        return jsonify({'message': field_status[1] + " field is missing"}), 400

    pwd_data = data['pwd']
    data.pop('pwd', None)

    encrypted_src = encrypt_credentials(data, Config.ENCRYPTION_KEY)
    encrypted_pwd = encrypt_credentials({'password': pwd_data}, Config.ENCRYPTION_KEY)
    
    remote_db = RemoteDatabases(src=encrypted_src, pwd=encrypted_pwd)
    db.session.add(remote_db)
    db.session.commit()

    return jsonify({'message': 'Credentials stored successfully'}), 200



if __name__ == '__main__':
    app.run()