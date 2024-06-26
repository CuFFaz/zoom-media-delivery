from decouple import config
from urllib.parse import quote_plus

class Config:
    DEBUG = False
    
    ENCRYPTION_KEY = b'Z-2tUU6ni8ZCR62hLDaHiwd3HhhfUvMFY86p8waproM='

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
        config('DB_ENGINE', default='mysql'),
        config('DB_USERNAME', default='central_db'),
        quote_plus(config('DB_PASS', default='Central#DB@123')),
        config('DB_HOST', default='172.31.16.78'),
        config('DB_PORT', default=3306),
        config('DB_NAME', default='central_db')
    )

    # SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
    #     config('DB_ENGINE', default='mysql'),
    #     config('DB_USERNAME', default='root'),
    #     quote_plus(config('DB_PASS', default='admin')),
    #     config('DB_HOST', default='127.0.0.1'),
    #     config('DB_PORT', default=3307),
    #     config('DB_NAME', default='central_db')
    # )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    scheduler_durations = {
                            "fetch_meetings_from_lms" :             10,                             # in seconds
                            "fetch_recordings_from_zoom" :          35,                             # in seconds                                
                            "fetch_recording_status_from_vimeo" :   30,                             # in seconds
                            "push_recording_link_to_lms" :          25,                             # in seconds
                        }
    
    zoom_token_url = 'https://zoom.us/oauth/token'
    zoom_grant_type = 'refresh_token'
    zoom_redirect_uri = 'https://corporate.digivarsity.com/'
    zoom_client_id = 'vZNKBhlgTrO_boj4qZHVpw'
    zoom_client_secret = 'B4PDzPtNtBPkjgrHsSvqmQteM1S2JNQ5'

    vimeo_url = "https://api.vimeo.com/me/videos"
    vimeo_status_url = 'https://api.vimeo.com/me'
    
class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    pass
