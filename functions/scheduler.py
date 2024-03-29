from models.models import RemoteDatabases
from functions.functions import decrypt_credentials
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.orm import scoped_session, sessionmaker

def remote_uri(decrypted_src, decrypted_pwd):
    return '{}://{}:{}@{}:{}/{}'.format(
        'mysql',
        decrypted_src['uname'],
        quote_plus(decrypted_pwd['password']),
        decrypted_src['host'],
        3306,
        decrypted_src['db_name']
    )

def fetch_meetings_from_lms():
    from app import app

    with app.app_context():
        print("scheduler start")
        credentials = RemoteDatabases.query.all()
        for cred in credentials:
            decrypted_src = decrypt_credentials(cred.src)
            decrypted_pwd = decrypt_credentials(cred.pwd)

            uri = remote_uri(decrypted_src, decrypted_pwd)
            print(uri)
            engine = create_engine(uri)
            remote_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

            get_meeting_query = '''SELECT z.meeting_id, z.course, z.name FROM mdl_zoom z
                                LEFT JOIN mdl_zoom_meeting_recordings_vimeo_ rv ON z.meeting_id = rv.meeting_id
                                WHERE z.meeting_id IS NOT NULL AND rv.meeting_id is NULL 
                                '''

            meeting_data = remote_session.execute(text(get_meeting_query)).mappings().all()[0]
            print(meeting_data)

            break

    return


def fetch_recordings_from_source():
    print("fetch_recordings_from_source!")

def push_recordings_to_dest():
    print("push_recordings_to_dest!")

def pull_recording_status_from_dest():
    print("pull_recording_status_from_dest!")