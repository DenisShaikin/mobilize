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
from time import time
import jwt
from flask import current_app as app
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
    category_filters = db.relationship('UserCatFilters', backref='User', lazy='dynamic', passive_deletes=True)  #Здесь будет список фильтров категорий на главной странице, типа {1:True, 2:False, 3:False}

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
        self.avatar_photo='/assets/img/team/profile-picture-1.jpg'

    def __repr__(self):
        return str(self.username)

    def set_password(self, value):
        if not isinstance(value, str):
            value = value[0]
        value = hash_pass(value)  # we need bytes here (not plain str)
        setattr (self, 'password', value)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return Users.query.get(id)

class UserCatFilters(db.Model):
    __tablename__ = 'Userfilters'

    id     = db.Column(db.Integer, primary_key=True)
    user   = db.Column(db.Integer, db.ForeignKey('Users.id', ondelete='CASCADE'))
    category = db.Column(db.Integer, db.ForeignKey('Categories.id', ondelete='CASCADE'))
    value   = db.Column(db.Boolean)
#инициализируем все пользовательские фильтры в True - все показываем
    def __init__(self, User, Category):
        self.user = User.id
        self.category = Category.id
        self.value = True

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
    name = db.Column(db.String(255))                             #Название предмета
    category = db.Column(db.Integer, ForeignKey("Categories.id"))
    description = db.Column(db.Text(20000))
    brand = db.Column(db.String(64))
    price = db.Column(db.Float, default=0)
    link = db.Column(db.String(128))
    video_link = db.Column(db.String(255))  #Ссылка на видео
    video_thumbnail = db.Column(db.String(255)) #Ссылка на превью ютуб видео
    photos = db.relationship('ItemPhotos', backref='Item', lazy='dynamic', passive_deletes=True, cascade='save-update, merge, delete')
    activities = db.relationship('Activity', backref='Item', lazy='dynamic', passive_deletes=True, cascade='save-update, merge, delete')
    comments = db.relationship('Comment', backref='Item', lazy='dynamic', passive_deletes=True, cascade='save-update, merge, delete')

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
            filter(Comment.item_id == self.id).order_by(Comment.timestamp.desc())

class ItemPhotos(db.Model):
    __tablename__ = 'ItemPhotos'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('Items.id', ondelete='CASCADE')) #Привязка к владельцу
    photo = db.Column(db.String(120))
    def __repr__(self):
        return self.photo
    def photos_id(self):
        return self.photo, self.id

class Posts(db.Model):
    __tablename__ = 'Posts'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id', ondelete='cascade')) #Привязка к Юзеру
    body = db.Column(db.Text(20000))
    photos = db.relationship('PostPhotos', backref='Item', lazy='dynamic', passive_deletes=True, cascade='save-update, merge, delete')
    parentPost = db.Column(db.Integer,  db.ForeignKey('Posts.id', ondelete='cascade')) #родительский пост
    def __repr__(self):
        return '<Post {}>'.format(self.body)
class PostPhotos(db.Model):
    __tablename__ = 'PostPhotos'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('Posts.id', ondelete='CASCADE')) #Привязка к владельцу
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
    item_id = db.Column(db.Integer, db.ForeignKey('Items.id', ondelete='cascade')) #Привязка к предметам
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id', ondelete='cascade')) #Привязка к предметам
    article_id = db.Column(db.Integer, db.ForeignKey('Articles.id', ondelete='cascade')) #Привязка к статьям
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
    article_id = db.Column(db.Integer, db.ForeignKey('Articles.id')) #Привязка к статьям
    text = db.Column(db.String(200))

    def __repr__(self):
        return '<Comment {}>'.format(self.text)


class Article(db.Model):
    __tablename__ = 'Articles'

    id = db.Column(db.Integer, primary_key=True)
    user_added = db.Column(db.Integer, ForeignKey("Users.id"))
    update_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    title = db.Column(db.String(255))                             #Название предмета
    body = db.Column(db.Text(40000))
    video_link = db.Column(db.String(255))  #Ссылка на видео
    video_thumbnail = db.Column(db.String(255)) #Ссылка на превью ютуб видео
    video_author = db.Column(db.String(100))
    video_description = db.Column(db.Text(1000))
    video_name = db.Column(db.String(255))
    video_uploadDate = db.Column(db.String(15))
    video_ageRestricted = db.Column(db.Boolean)
    video_duration =db.Column(db.String(50))
    activities = db.relationship('Activity', backref='Article', lazy='dynamic', passive_deletes=True)
    comments = db.relationship('Comment', backref='Article', lazy='dynamic', passive_deletes=True)
    photos = db.relationship('ArticlePhotos', backref='Article', lazy='dynamic', passive_deletes=True)

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
        return str(self.title)

    def followed_comments(self, User):
        #Сперва удалим пустые других пользователей
        if User:
            db.session.query(Comment).filter((Comment.text=='') & (Comment.user_id != User.id)).delete()
            db.session.commit()
        return Comment.query.join(Users, Users.id==Comment.user_id).\
            with_entities(Comment.id, Users.username, Comment.text).\
            filter(Comment.article_id == self.id).order_by(Comment.timestamp.desc())

    def add_emptycomment(self, User):
        '''Функция проверяет наличие пустого комментария и его возвращает, если его нет - создает'''

        if not self.is_emptycommentexist(User):
            newComment=Comment(user_id=User.id, article_id=self.id, text='')
            self.comments.append(newComment)
            db.session.commit()
            return newComment
        else:
            return Comment.query.filter((Comment.user_id==User.id) & (Comment.article_id==self.id) &
                                        (Comment.text=='')).first()

    def is_emptycommentexist(self, User):
        return self.comments.filter((Comment.article_id == self.id) &
                                    (Comment.user_id == User.id) &
                                    (Comment.text == '')).count() > 0

class ArticlePhotos(db.Model):
    __tablename__ = 'ArticlePhotos'

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('Articles.id', ondelete='CASCADE')) #Привязка к владельцу
    photo = db.Column(db.String(120))
    def __repr__(self):
        return self.photo
    def photos_id(self):
        return self.photo, self.id
