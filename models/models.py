from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class RemoteDatabases(db.Model):
    __tablename__ = 'remotes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    src = db.Column(db.Text)
    pwd = db.Column(db.Text)

class Sources(db.Model):
    __tablename__ = 'sources'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lms_id = db.Column(db.Integer)
    course_id = db.Column(db.Integer)
    meeting_id = db.Column(db.Integer)
    meeting_name = db.Column(db.Text)

class Recording(db.Model):
    __tablename__ = 'recordings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    source_id = db.Column(db.Integer)
    lms_id = db.Column(db.Integer)
    course_id = db.Column(db.Integer)
    meeting_id = db.Column(db.Integer)
    meeting_name = db.Column(db.Text)
    zoom_recording_uuid = db.Column(db.String(255))
    zoom_recording_download_url = db.Column(db.Text)
    zoom_recording_download_password = db.Column(db.String(255))
    vimeo_id = db.Column(db.String(255))
    vimeo_link = db.Column(db.Text)
    vimeo_player_embed_url = db.Column(db.Text)
    upload_status = db.Column(db.String(50))
    transcoding_status = db.Column(db.String(50))
    process_status = db.Column(db.String(50))
    play_status = db.Column(db.String(50))
    status = db.Column(db.Integer)
    timecreated = db.Column(db.Integer)
    timemodified = db.Column(db.Integer)
    comment = db.Column(db.Text)

    def __repr__(self):
        return f"<Recording(id={self.id}, meeting_name='{self.meeting_name}')>"

class SchedulerLog(db.Model):
    __tablename__ = 'scheduler_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scheduler_name = db.Column(db.String(100))
    start_time = db.Column(db.Integer)
    end_time = db.Column(db.Integer)
    retry_count = db.Column(db.Integer)
    connection_status = db.Column(db.Integer)
    status = db.Column(db.Integer)
    error = db.Column(db.Text)

    def __repr__(self):
        return f"<SchedulerLog(id={self.id}, scheduler_name='{self.scheduler_name}', status='{self.status}')>"