# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, BooleanField, RadioField, MultipleFileField, TextAreaField, DateField
from wtforms.validators import Email, DataRequired, NumberRange
from flask_wtf.file import  FileRequired, FileAllowed

class SettingsForm(FlaskForm):
    first_name = StringField('Имя', id='first_name')
    last_name = StringField('Фамилия', id='last_name')
    burth_date = DateField('Дата', format='%Y-%m-%d' )
    # StringField('ДР', id='burth_date')


class AddItemForm(FlaskForm):
    name = StringField('Объект',
                         id='name_additem',
                         validators=[DataRequired()])
    category = SelectField('Категория',
                           id='category_additem',
                           validate_choice=False, coerce=int)
    description = TextAreaField('Описание', id='description_additem')
    brand = StringField('Бренд', id = 'brand_additem')
    price = DecimalField('Цена', validators=[NumberRange(min=0, message='Проверьте число!')])
    link = StringField('Ссылка', id = 'link_additem')
    photos = MultipleFileField('Выберите файлы с фото', validators=[FileRequired(),
                                    FileAllowed(['png', 'jpg', 'bmp'], "Некорректный формат!")])
    inList = BooleanField('Включить в список', default=True)
    haveIt = BooleanField('Есть в наличии', default=True)
    rating = RadioField('rating', choices=[('5', '5 stars'), ('4', '4 stars'), ('3', '3 stars'), ('2', '2 stars'), ('1', '1 star')],
                       coerce = int)

class EditItemForm(FlaskForm):
    name = StringField('Объект',
                         id='name_additem',
                         validators=[DataRequired()])
    category = SelectField('Категория',
                           id='category_additem',
                           validate_choice=False, coerce=int)
    description = TextAreaField('Описание', id='description_additem')
    brand = StringField('Бренд', id = 'brand_additem')
    price = DecimalField('Цена', validators=[NumberRange(min=0, message='Проверьте число!')])
    link = StringField('Ссылка', id = 'link_additem')
    photos = MultipleFileField('Выберите файлы с фото', validators=[FileAllowed(['png', 'jpg', 'bmp'], "Некорректный формат!")])
    inList = BooleanField('Включить в список', default=True)
    haveIt = BooleanField('Есть в наличии', default=True)
    rating = RadioField('rating', choices=[('5', '5 stars'), ('4', '4 stars'), ('3', '3 stars'), ('2', '2 stars'), ('1', '1 star')],
                       coerce = int)
