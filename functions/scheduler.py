from models.models import RemoteDatabases, Meetings, EndpointTokens, Recording, SchedulerLog
from functions.functions import decrypt_credentials, get_unix_time, get_unix_yesterday
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
import json

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
    from app import app, db

    cron_status = True
    comment = ""
    start = get_unix_time()

    with app.app_context():
        print("scheduler start")
        credentials = RemoteDatabases.query.all()
        try:
            for cred in credentials:
                decrypted_src = decrypt_credentials(cred.src)
                decrypted_pwd = decrypt_credentials(cred.pwd)

                uri = remote_uri(decrypted_src, decrypted_pwd)
                engine = create_engine(uri)
                remote_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

                get_meeting_query = '''SELECT z.meeting_id, z.course, z.name FROM mdl_zoom z
                                    WHERE unix_timestamp(z.created_at) >= :current_date_unix
                                    '''

                meeting_data = remote_session.execute(text(get_meeting_query), {"current_date_unix": get_unix_yesterday()}).mappings().all()
                if meeting_data:
                    for item in meeting_data:
                        saved_meetings = db.session.query(Meetings).filter_by(meeting_id=item['meeting_id']).first()
                        if saved_meetings:
                            comment += f"Meeting {item['meeting_id']} already added! \n"
                            continue
                        meeting = Meetings(
                            remote_id=cred.id,
                            course_id=item['course'],
                            meeting_id=item['meeting_id'],
                            meeting_name=item['name'],
                            meeting_process_status=0
                        )
                        db.session.add(meeting)
                else:
                    comment += "No new meeting data found in " + decrypted_src['db_name'] + "\n"
        except Exception as e:
            cron_status = False
            comment = e

        logging = SchedulerLog(
            scheduler_name = "fetch_meetings_from_lms",
            start_time = start,
            end_time = get_unix_time(),
            retry_count = 0,
            status = "success" if cron_status else "failed",
            exceptions = comment
        )
        db.session.add(logging)
        db.session.commit()
        print("scheduler end")

    return


def fetch_recordings_from_source():
    from app import app, db

    cron_status = True
    comment = ""
    start = get_unix_time()
    processed_meetings = []
    failed_meetings = []

    with app.app_context():
        try:
            print("scheduler start")
            zoom_token_url = 'https://zoom.us/oauth/token'
            zoom_grant_type = 'refresh_token'
            zoom_redirect_uri = 'https://corporate.digivarsity.com/'
            zoom_client_id = 'vZNKBhlgTrO_boj4qZHVpw'
            zoom_client_secret = 'B4PDzPtNtBPkjgrHsSvqmQteM1S2JNQ5'
            vimeo_url = "https://api.vimeo.com/me/videos"

            refresh_token_starttime_unix = get_unix_time()
            refresh_token_endtime_unix = get_unix_time()
            zoom_token_expiry_duration = 3600               # Assuming 1 hour expiry duration

            meetings_with_status = Meetings.query.filter_by(meeting_process_status=0).all()

            for meeting in meetings_with_status:
                processed_meetings.append(meeting.meeting_id)

                try:
                    token_regen_flag = 0

                    if token_regen_flag == 0:
                        refresh_token = db.session.query(EndpointTokens.token_value).filter_by(token_type='refresh_token').first()[0]

                        url = f"{zoom_token_url}?grant_type={zoom_grant_type}&redirect_uri={zoom_redirect_uri} \
                                &refresh_token={refresh_token}&client_id={zoom_client_id}&client_secret={zoom_client_secret}"

                        response = requests.post(url)
                        response_json = response.json()

                        if ('refresh_token' in response_json) and ('access_token' in response_json):

                            access_token = response_json['access_token']
                            refresh_token = response_json['refresh_token']

                            access_token_instance = db.session.query(EndpointTokens).filter_by(token_type='access_token').first()
                            refresh_token_instance = db.session.query(EndpointTokens).filter_by(token_type='refresh_token').first()

                            access_token_instance.token_value = access_token
                            refresh_token_instance.token_value = refresh_token

                            access_token_instance.updated_time = get_unix_time()
                            refresh_token_instance.updated_time = get_unix_time()
                            db.session.commit()
                        else:
                            raise Exception
                    else:
                        access_token = db.session.query(EndpointTokens.token_value).filter_by(token_type='access_token').first()[0]

                except Exception as e:
                    cron_status = False
                    comment = "Zoom token regen failed! Exception : " + str(e)
                    break

                if (refresh_token_endtime_unix - refresh_token_starttime_unix) >= zoom_token_expiry_duration:
                    refresh_token_starttime_unix = get_unix_time()
                    token_regen_flag = 0
                else:
                    token_regen_flag = 1

                try:
                    zoom_url = f"https://api.zoom.us/v2/meetings/{meeting.meeting_id}/recordings?include_fields=download_access_token"
                    headers = {
                        'Authorization': f'Bearer {access_token}',
                    }
                    zoom_response = requests.request("GET", zoom_url, headers=headers).json()

                    if 'code' in zoom_response and zoom_response['code'] == 124:  # INVALID TOKEN ERROR
                        cron_status = False
                        comment += f"Invalid token error while processing Meeting ID : {meeting.meeting_id} \n"
                        failed_meetings.append(meeting.meeting_id)
                        continue

                    if 'code' in zoom_response and zoom_response['code'] == 3301:  # RECORDING NOT AVAILABLE
                        cron_status = False
                        comment += f"Recording not found while processing Meeting ID : {meeting.meeting_id} \n"
                        failed_meetings.append(meeting.meeting_id)
                        continue

                    # get only mp4 recordings
                    mp4_recordings = [file for file in zoom_response['recording_files'] if file.get('file_type') == 'MP4']

                    if mp4_recordings:
                        mp4_recording = mp4_recordings[0]
                        recording_link_token = zoom_response['download_access_token']
                        recording_size = mp4_recording['file_size']
                        recording_link = mp4_recording['download_url']
                    else:
                        cron_status = False
                        comment += f"MP4 recording not found on zoom while processing Meeting ID : {meeting.meeting_id} \n"
                        failed_meetings.append(meeting.meeting_id)
                        continue

                except Exception as e:
                    cron_status = False
                    comment += f"Zoom API request failed while processing Meeting ID : {meeting.meeting_id} - Exception : "+ str(e) +"\n"
                    failed_meetings.append(meeting.meeting_id)
                    continue

                try:
                    vimeo_token = db.session.query(EndpointTokens.token_value).filter_by(token_type='vimeo_token').first()[0]
                    payload = json.dumps({
                        "upload": {
                            "approach": "pull",
                            "size": recording_size,
                            "link": recording_link + '?access_token=' + recording_link_token
                        }
                    })
                    headers = {
                        'Authorization': f'Bearer {vimeo_token}',
                        'Content-Type': 'application/json',
                    }

                    vimeo_response = requests.request("POST", vimeo_url, headers=headers, data=payload).json()

                    if 'error_code' in vimeo_response and vimeo_response['error_code'] == 4101:  # Insufficient space on vimeo error
                        cron_status = False
                        comment += f"Insufficient space on vimeo while processing Meeting ID : {meeting.meeting_id} \n"
                        failed_meetings.append(meeting.meeting_id)
                        continue

                except Exception as e:
                    cron_status = False
                    comment += f"Vimeo API request failed while processing Meeting ID : {meeting.meeting_id} - Exception : "+ str(e) + "\n"
                    failed_meetings.append(meeting.meeting_id)
                    continue

                try:
                    recording = Recording(
                                remote_id = meeting.remote_id,
                                course_id = meeting.course_id,
                                meeting_id = meeting.meeting_id,
                                meeting_name = meeting.meeting_name,
                                zoom_recording_uuid = zoom_response['uuid'],
                                zoom_recording_download_url = recording_link,
                                zoom_recording_download_password = zoom_response['password'],
                                vimeo_id = vimeo_response['uri'],
                                vimeo_link = vimeo_response['link'],
                                vimeo_player_embed_url = vimeo_response['player_embed_url'],
                                upload_status = vimeo_response['upload']['status'],
                                transcoding_status = vimeo_response['transcode']['status'],
                                process_status = vimeo_response['status'],
                                play_status = vimeo_response['play']['status'],
                                status = 0,
                                timecreated = get_unix_time(),
                                timemodified = get_unix_time()
                            )
                    db.session.add(recording)

                    meeting_update = Meetings.query.filter_by(meeting_id=meeting.meeting_id).first()
                    meeting_update.meeting_process_status = 1
                except Exception as e:
                    cron_status = False
                    comment += f"Failed while inserting Meeting ID : {meeting.meeting_id} - Exception : "+ str(e) + "\n"
                    failed_meetings.append(meeting.meeting_id)
                    continue

            db.session.commit()
        except Exception as e:
            cron_status = False
            comment = e

        logging = SchedulerLog(
            scheduler_name = "fetch_recordings_from_source",
            start_time = start,
            end_time = get_unix_time(),
            retry_count = 0,
            processed_meetings = ', '.join(processed_meetings) if processed_meetings else None,
            failed_meetings = ', '.join(failed_meetings) if failed_meetings else None,
            status = "success" if cron_status else "failed",
            exceptions = comment if comment else None
        )
        db.session.add(logging)
        db.session.commit()

    print("scheduler end")
    return

def pull_recording_status_from_dest():
    from app import app, db

    cron_status = True
    comment = ""
    processed_meetings = []
    failed_meetings = []
    start = get_unix_time()

    with app.app_context():
        print("scheduler start")
        vimeo_status_url = 'https://api.vimeo.com/me'
        
        recording_with_status = Recording.query.filter_by(status=0).all()
        for recording in recording_with_status: 
            processed_meetings.append(recording.meeting_id)
            try:
                recording_status = 0
                vimeo_status_url = vimeo_status_url + recording.vimeo_id
                vimeo_token = db.session.query(EndpointTokens.token_value).filter_by(token_type='vimeo_token').first()[0]

                headers = {
                    'Authorization': 'Bearer ' + vimeo_token
                }

                response = requests.get(vimeo_status_url, headers=headers)
                response_json = response.json()

                if 'error' not in response_json:
                    if (response_json['upload']['status'] == "complete" and 
                        response_json['transcode']['status'] == "complete" and 
                        response_json['status'] == "available" and 
                        response_json['play']['status'] == "playable"):
                        recording_status = 1

                    recording_instance = db.session.query(Recording).filter_by(id=recording.id).first()
                    recording_instance.upload_status = response_json['upload']['status']
                    recording_instance.transcoding_status = response_json['transcode']['status']
                    recording_instance.process_status = response_json['status']
                    recording_instance.play_status = response_json['play']['status']
                    recording_instance.status = recording_status
                    recording_instance.timemodified = get_unix_time()
                    db.session.commit()
                else:
                    cron_status = False
                    comment += f"Vimeo return an error at recording_id : {recording.id} - Error : "+ response_json['error'] +" \n"
                    failed_meetings.append(recording.meeting_id)
                    continue

            except Exception as e:
                cron_status = False
                comment += f"Something went wrong while updating vimeo status at recording_id : {recording.id} - Exception : "+ str(e) +" \n"
                failed_meetings.append(recording.meeting_id)
                continue

        logging = SchedulerLog(
            scheduler_name = "pull_recording_status_from_dest",
            start_time = start,
            end_time = get_unix_time(),
            retry_count = 0,
            processed_meetings = ', '.join(processed_meetings) if processed_meetings else None,
            failed_meetings = ', '.join(failed_meetings) if failed_meetings else None,
            status = "success" if cron_status else "failed",
            exceptions = comment if comment else None
        )
        db.session.add(logging)
        db.session.commit()

    print("scheduler end")
    return

def push_recording_to_source():
    from app import app, db

    cron_status = True
    comment = ""
    processed_meetings = []
    failed_meetings = []
    start = get_unix_time()

    with app.app_context():
        print("scheduler start")

        recording_with_status = Recording.query.filter_by(lms_push_status=0, status=1).all()
        for recording in recording_with_status:
            processed_meetings.append(recording.meeting_id)
            try:
                remote_creds = db.session.query(RemoteDatabases).filter_by(id=recording.remote_id).first()

                decrypted_src = decrypt_credentials(remote_creds.src)
                decrypted_pwd = decrypt_credentials(remote_creds.pwd)

                uri = remote_uri(decrypted_src, decrypted_pwd)
                engine = create_engine(uri)

                remote_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
                insert_recording_query = '''INSERT INTO mdl_zoom_vimeo_recordings_mapping
                    (meeting_id, vimeo_link, vimeo_player_embed_url, created_time) VALUES (
                    :meeting_id, :vimeo_link, :vimeo_player_embed_url, :created_time)'''

                params = {
                        "meeting_id": recording.meeting_id,
                        "vimeo_link": recording.vimeo_link,
                        "vimeo_player_embed_url": recording.vimeo_player_embed_url,
                        "created_time": get_unix_time()
                        }

                remote_session.execute(text(insert_recording_query), params)
                remote_session.commit()
                
                recording_instance = db.session.query(Recording).filter_by(id=recording.id).first()
                recording_instance.lms_push_status = 1
                db.session.commit()
            except Exception as e:
                cron_status = False
                comment += f"Something went wrong while pushing recording_id : {recording.id} to lms - Exception :"+ str(e) +" \n"
                failed_meetings.append(recording.meeting_id)
                continue

        logging = SchedulerLog(
            scheduler_name = "push_recording_to_source",
            start_time = start,
            end_time = get_unix_time(),
            retry_count = 0,
            processed_meetings = ', '.join(processed_meetings) if processed_meetings else None,
            failed_meetings = ', '.join(failed_meetings) if failed_meetings else None,
            status = "success" if cron_status else "failed",
            exceptions = comment if comment else None
        )
        db.session.add(logging)
        db.session.commit()

    print("scheduler end")
    return