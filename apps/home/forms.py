# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, FloatField
from wtforms.validators import Email, DataRequired

# login and registration


class LoginForm(FlaskForm):
    username = StringField('Username',
                         id='username_login',
                         validators=[DataRequired()])
    password = PasswordField('Password',
                             id='pwd_login',
                             validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    username = StringField('Username',
                         id='username_create',
                         validators=[DataRequired()])
    email = StringField('Email',
                      id='email_create',
                      validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             id='pwd_create',
                             validators=[DataRequired()])


class AddItemForm(FlaskForm):
    name = StringField('Объект',
                         id='name_additem',
                         validators=[DataRequired()])
    category = SelectField('Категория',
                           id='category_additem',
                           validate_choice=False, coerce=int)
    description = StringField('Описание', id='description_additem')
    brand = StringField('Бренд', id = 'brand_additem')
    price = FloatField('Цена', default=0)
    link = StringField('Ссылка', id = 'link_additem')
    submit = SubmitField('Отправить')