from decouple import config
from urllib.parse import quote_plus

class Config:
    DEBUG = False
    
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
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    pass
