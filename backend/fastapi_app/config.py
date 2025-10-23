import os
from typing import List

# Keep names similar to original Flask app for easier migration
AD_SERVER = os.getenv('AD_SERVER', 'ldap://CLODC02.snm.local')
AD_USERNAME = os.getenv('AD_USERNAME', 'SNM\\adm.itservices')
AD_PASSWORD = os.getenv('AD_PASSWORD', 'xmZ7P@5vkKzg')
AD_BASE_DN = os.getenv('AD_BASE_DN', 'DC=snm,DC=local')

DELL_CLIENT_ID = os.getenv('DELL_CLIENT_ID', 'l75c9d200744a444a08c54b666ddbd9b1a')
DELL_CLIENT_SECRET = os.getenv('DELL_CLIENT_SECRET', '5a6bfc5dd76c40a6bd8b896c6ab63e9e')


SQL_SERVER = os.getenv('SQL_SERVER', 'CLOSQL02')
SQL_DATABASE = os.getenv('SQL_DATABASE', 'DellReports')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')
USE_WINDOWS_AUTH = os.getenv('USE_WINDOWS_AUTH', 'true').lower() == 'true'

class Settings:
    def __init__(self):
        self.AD_SERVER = AD_SERVER
        self.AD_USERNAME = AD_USERNAME
        self.AD_PASSWORD = AD_PASSWORD
        self.AD_BASE_DN = AD_BASE_DN

        self.DELL_CLIENT_ID = DELL_CLIENT_ID
        self.DELL_CLIENT_SECRET = DELL_CLIENT_SECRET

        self.SQL_SERVER = SQL_SERVER
        self.SQL_DATABASE = SQL_DATABASE
        self.SQL_USERNAME = SQL_USERNAME
        self.SQL_PASSWORD = SQL_PASSWORD
        self.USE_WINDOWS_AUTH = USE_WINDOWS_AUTH

        # CORS defaults mirrored from Flask app
        self.CORS_ORIGINS: List[str] = os.getenv('CORS_ORIGINS', '*').split(',') if os.getenv('CORS_ORIGINS') else ["*"]
        self.CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        self.CORS_HEADERS = ["Content-Type", "Authorization", "Accept", "X-Requested-With", "Origin"]
        self.CORS_CREDENTIALS = False
        self.CORS_MAX_AGE = 86400


settings = Settings()
