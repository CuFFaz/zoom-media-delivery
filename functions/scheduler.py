from models.models import RemoteDatabases
from functions.functions import decrypt_credentials

def fetch_meetings_from_lms():
    from app import app

    with app.app_context():
        print("scheduler start")
        credentials = RemoteDatabases.query.all()
        for cred in credentials:
            decrypted_src = decrypt_credentials(cred.src)
            decrypted_pwd = decrypt_credentials(cred.pwd)

            print(decrypted_src)
            print(decrypted_pwd)

    return

    # sql = '''SELECT z.meeting_id, z.course, z.name FROM mdl_zoom z
    #         LEFT JOIN mdl_zoom_meeting_recordings_vimeo_ rv ON z.meeting_id = rv.meeting_id
    #         WHERE z.meeting_id IS NOT NULL AND rv.meeting_id is NULL 
    #         AND unix_timestamp(z.created_at) >= :current_date_unix'''


    print("fetch_meetings_from_lms!")

def fetch_recordings_from_source():
    print("fetch_recordings_from_source!")

def push_recordings_to_dest():
    print("push_recordings_to_dest!")

def pull_recording_status_from_dest():
    print("pull_recording_status_from_dest!")