# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from datetime import timedelta

class Config(object):

    basedir = os.path.abspath(os.path.dirname(__file__))

    # Set up the App SECRET_KEY
    # SECRET_KEY = config('SECRET_KEY'  , default='S#perS3crEt_007')
    SECRET_KEY = os.getenv('SECRET_KEY', 'S#perPuperS3crEt_013')

    # This will create a file in <app> FOLDER
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'sqlite3.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False 

    # Assets Management
    ASSETS_ROOT = os.getenv('ASSETS_ROOT', '/static/assets')    
    
    SOCIAL_AUTH_GITHUB  = False

    ITEMS_PER_PAGE = 30
    COMMENTS_PER_PAGE = 3
    ARTICLES_PER_PAGE = 9

    PHOTOS_FOLDER = os.path.join('assets', 'img', 'photos')
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'assets', 'img', 'photos')
    PERSO_PHOTO_FOLDER = os.path.join(basedir, 'static', 'assets', 'img', 'team')
    PERSO_PHOTO = os.path.join('assets', 'img', 'team')
    ITEMFILES_PATH = os.path.join(basedir, 'static', 'assets', 'uploads')
    FILES_PATH = os.path.join('assets', 'uploads')

    # JWT_COOKIE_SECURE = False
    # JWT_TOKEN_LOCATION = "cookies"
    # JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    CKEDITOR_PKG_TYPE = 'standard'
    CKEDITOR_SERVE_LOCAL = True
    CKEDITOR_HEIGHT = 300
    CKEDITOR_FILE_UPLOADER= 'home_blueprint.upload'
    UPLOADED_PATH = os.path.join(basedir, 'static', 'assets', 'uploads')

    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT') or 25)
    MAIL_USE_SSL = True #os.environ.get('MAIL_USE_SSL')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    ADMINS = ['chaikide@mail.ru']

    GITHUB_ID      = os.getenv('GITHUB_ID')
    GITHUB_SECRET  = os.getenv('GITHUB_SECRET')

    # Enable/Disable Github Social Login    
    if GITHUB_ID and GITHUB_SECRET:
         SOCIAL_AUTH_GITHUB  = True
             
class ProductionConfig(Config):
    DEBUG = False

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    # PostgreSQL database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
    #     os.getenv('DB_ENGINE'   , 'mysql'),
    #     os.getenv('DB_USERNAME' , 'appseed_db_usr'),
    #     os.getenv('DB_PASS'     , 'pass'),
    #     os.getenv('DB_HOST'     , 'localhost'),
    #     os.getenv('DB_PORT'     , 3306),
    #     os.getenv('DB_NAME'     , 'appseed_db')
    # )


class DebugConfig(Config):
    DEBUG = True
    basedir = os.path.abspath(os.path.dirname(__file__))

# Load all possible configurations
config_dict = {
    'Production': ProductionConfig,
    'Debug'     : DebugConfig
}
