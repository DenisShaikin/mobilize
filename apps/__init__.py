# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_wtf.csrf import CSRFProtect
from flask_ckeditor import CKEditor
from flask_mail import Mail
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection
import sqlalchemy as sa
from flask_moment import Moment


db = SQLAlchemy()
login_manager = LoginManager()
ckeditor = CKEditor()
csrf = CSRFProtect()
mail = Mail()
moment = Moment()


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    moment.init_app(app)

def register_blueprints(app):
    for module_name in ('authentication', 'home'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app):

    @app.before_first_request
    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()

from apps.authentication.oauth import github_blueprint

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    ckeditor.init_app(app)

    app.register_blueprint(github_blueprint, url_prefix="/login") 
    
    configure_database(app)
    #Включаем каскадное удаление

    return app

@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()