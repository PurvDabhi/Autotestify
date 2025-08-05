# import os
# from dotenv import load_dotenv

# load_dotenv()

# class Config:
#     SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
#     # GitHub API
#     GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
    
#     # Gemini API
#     GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
#     # Email Configuration
#     MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
#     MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
#     MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
#     MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
#     MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
#     MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
#     # Application Settings
#     MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # GitHub API
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
    
    # Gemini API
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # Mailjet Email Configuration
    MAILJET_API_KEY = os.environ.get('MAILJET_API_KEY')
    MAILJET_API_SECRET = os.environ.get('MAILJET_API_SECRET')
    MAILJET_SENDER_EMAIL = os.environ.get('MAILJET_SENDER_EMAIL')  # Must be verified in Mailjet
    MAILJET_SENDER_NAME = os.environ.get('MAILJET_SENDER_NAME', 'AutoTestify')
    
    # Application Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
