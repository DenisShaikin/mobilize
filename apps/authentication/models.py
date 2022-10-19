# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import UserMixin

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from datetime import datetime, timedelta
from apps import db, login_manager

from apps.authentication.util import hash_pass

class Users(db.Model, UserMixin):

    __tablename__ = 'Users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64), unique=True)
    email         = db.Column(db.String(64), unique=True)
    password      = db.Column(db.LargeBinary)
    first_name    = db.Column(db.String(64))
    last_name     = db.Column(db.String(64))
    burth_date    = db.Column(db.DateTime)
    avatar_photo = db.Column(db.String(100))

    oauth_github  = db.Column(db.String(100), nullable=True)
    activities = db.relationship('Activity', backref='User', lazy='dynamic', passive_deletes=True)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username) 

@login_manager.user_loader
def user_loader(id):
    return Users.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = Users.query.filter_by(username=username).first()
    return user if user else None

class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id", ondelete="cascade"), nullable=False)
    user = db.relationship(Users)


class Item(db.Model):
    __tablename__ = 'Items'

    id = db.Column(db.Integer, primary_key=True)
    user_added = db.Column(db.Integer, ForeignKey("Users.id"))
    update_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    name = db.Column(db.String(64))                             #Название предмета
    category = db.Column(db.Integer, ForeignKey("Categories.id"))
    description = db.Column(db.String(255))
    brand = db.Column(db.String(64))
    price = db.Column(db.Float)
    link = db.Column(db.String(128))
    photos = db.relationship('ItemPhotos', backref='Item', lazy='dynamic', passive_deletes=True)
    activities = db.relationship('Activity', backref='Item', lazy='dynamic', passive_deletes=True)
    comments = db.relationship('Comment', backref='Item', lazy='dynamic', passive_deletes=True)

    def __init__(self, **kwargs):  #Создание элемента по словарю аргументов
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]
            setattr(self, property, value)
    def __repr__(self):
        return str(self.name)

    def add_comment(self, comment):
        if not self.is_commentexist(comment):
            self.comments.append(comment)

    def add_emptycomment(self, User):
        '''Функция проверяет наличие пустого комментария и его возвращает, если его нет - создает'''

        if not self.is_emptycommentexist(User):
            newComment=Comment(user_id=User.id, item_id=self.id, text='')
            self.comments.append(newComment)
            db.session.commit()
            return newComment
        else:
            return Comment.query.filter((Comment.user_id==User.id) & (Comment.item_id==self.id) &
                                        (Comment.text=='')).first()

    def is_emptycommentexist(self, User):
        return self.comments.filter((Comment.item_id == self.id) &
                                    (Comment.user_id == User.id) &
                                    (Comment.text == '')).count() > 0

    def is_commentexist(self, comment):
        return self.comments.filter(
            comment.c.item_id == self.id).count() > 0

    def followed_comments(self, User):
        #Сперва удалим пустые других пользователей
        db.session.query(Comment).filter((Comment.text=='') & (Comment.user_id != User.id)).delete()
        db.session.commit()
        return Comment.query.join(Users, Users.id==Comment.user_id).\
            with_entities(Comment.id, Users.username, Comment.text).\
            filter(Comment.item_id == self.id).order_by(Comment.timestamp.asc())

class ItemPhotos(db.Model):
    __tablename__ = 'ItemPhotos'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('Items.id', ondelete='CASCADE')) #Привязка к владельцу
    photo = db.Column(db.String(120))
    def __repr__(self):
        return self.photo
    def photos_id(self):
        return self.photo, self.id


class Category(db.Model):
    __tablename__ = 'Categories'

    id = db.Column(db.Integer, primary_key=True)
    catname = db.Column(db.String(64))
    def __repr__(self):
        return str(self.catname)

class Activity(db.Model):
    __tablename__ = 'Activity'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('Items.id')) #Привязка к предметам
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id')) #Привязка к предметам
    rating = db.Column(db.Integer)  #Оценка от 1 до 5
    inList = db.Column(db.Boolean) #Включить в список
    haveIt = db.Column(db.Boolean) #Уже есть в наличии
    def __repr__(self):
        return str(self.id)


class ActivityPhotos(db.Model):
    __tablename__ = 'ActivityPhotos'

    id = db.Column(db.Integer, primary_key=True)
    activ_id = db.Column(db.Integer, db.ForeignKey('Activity.id', ondelete='CASCADE')) #Привязка к владельцу
    photo = db.Column(db.String(120))
    def __repr__(self):
        return self.photo

class Comment(db.Model):  #Комментарии к Items
    __tablename__ = 'Comment'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))  # Привязка к пользователю
    item_id = db.Column(db.Integer, db.ForeignKey('Items.id')) #Привязка к предметам
    text = db.Column(db.String(200))

    def __repr__(self):
        return '<Comment {}>'.format(self.text)