from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from config import DevelopmentConfig, ProductionConfig
from models.models import db, Meetings, Recording, SchedulerLog, RemoteDatabases
from functions.scheduler import fetch_meetings_from_lms, fetch_recordings_from_source, \
                                pull_recording_status_from_dest, push_recording_to_source
from functions.functions import encrypt_credentials
from config import Config
import atexit

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
# app.config.from_object(ProductionConfig)

db.init_app(app)

with app.app_context():
    db.create_all()

# APScheduler setup
scheduler = BackgroundScheduler()
scheduler.start()

# job_defaults = {
#     'coalesce': False,
#     'max_instances': 1
# }
# scheduler.configure(job_defaults=job_defaults)

# scheduler.add_job(fetch_meetings_from_lms, 'cron', hour=Config.scheduler_durations['fetch_meetings_from_lms']['hour']
#                                                 , minute=Config.scheduler_durations['fetch_meetings_from_lms']['minute'])
scheduler.add_job(fetch_recordings_from_source, 'interval', seconds=Config.scheduler_durations['fetch_recordings_from_zoom'])
scheduler.add_job(pull_recording_status_from_dest, 'interval', seconds=Config.scheduler_durations['fetch_recording_status_from_vimeo'])
scheduler.add_job(push_recording_to_source, 'interval', seconds=Config.scheduler_durations['push_recording_link_to_lms'])

atexit.register(lambda: scheduler.shutdown())

def mandatory_keyval_empty_check(data, keys):
    for key in keys:
        if key not in data:
            return [False, key]
        elif data[key] == "":
            return [False, key]
    return [True, True]

@app.route('/')
def index():
    return 'Running!'

@app.route('/add', methods=['POST'])
def store_credentials():
    data = request.json

    field_status = mandatory_keyval_empty_check(data, ["host", "uname", "pwd", "db_name", "port"])
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
    app.run(use_reloader=False)