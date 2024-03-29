from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from config import DevelopmentConfig, ProductionConfig
from models.models import db, Sources, Recording, SchedulerLog, RemoteDatabases
from scheduler.scheduler import fetch_meetings_from_lms, fetch_recordings_from_source, \
                                push_recordings_to_dest, pull_recording_status_from_dest
from cryptography.fernet import Fernet

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

scheduler.add_job(fetch_meetings_from_lms, 'interval', seconds=10)
scheduler.add_job(fetch_recordings_from_source, 'interval', seconds=10)
scheduler.add_job(push_recordings_to_dest, 'interval', seconds=10)
scheduler.add_job(pull_recording_status_from_dest, 'interval', seconds=10)
atexit.register(lambda: scheduler.shutdown())

# Encryption key
ENCRYPTION_KEY = b'56e3c1d15b8b7b424a4a975d114f2f69c27a93810b0deb7da7929faaf6958440'

# Encrypting function
def encrypt_credentials(credentials_dict, key):
    plain_text = json.dumps(credentials_dict)
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(plain_text.encode()).decode()


@app.route('/')
def index():
    return 'Running!'

@app.route('/add', methods=['POST'])
def store_credentials():
    data = request.json
    if 'src' in data and 'pwd' in data:
        src_data = data['src']
        pwd_data = data['pwd']

        # Encrypt source data
        encrypted_src = encrypt_credentials(src_data, ENCRYPTION_KEY)
        # Encrypt password
        encrypted_pwd = encrypt_credentials({'password': pwd_data}, ENCRYPTION_KEY)
        
        # Store encrypted data in the database
        remote_db = RemoteDatabases(src=encrypted_src, pwd=encrypted_pwd)
        db.session.add(remote_db)
        db.session.commit()
        
        return jsonify({'message': 'Credentials stored successfully'}), 201
    else:
        return jsonify({'error': 'Incomplete data provided'}), 400

if __name__ == '__main__':
    app.run()