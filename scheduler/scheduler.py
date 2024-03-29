

def fetch_meetings_from_lms():



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