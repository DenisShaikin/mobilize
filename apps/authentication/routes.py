# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, redirect, request, url_for

from flask_login import (
    current_user,
    login_user,
    logout_user
)

from flask_dance.contrib.github import github
from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users
from apps.authentication.forms import ResetPasswordRequestForm, ResetPasswordForm
from apps.authentication.email import send_password_reset_email
from apps.authentication.util import verify_pass
from apps.authentication.models import Users, Category, UserCatFilters, CategoryPhotos
from datetime import datetime, timedelta
from flask import current_app as app
from apps.authentication.pseudo_loginDB import PseudoUser
from sqlalchemy import update, values
from apps.authentication.util import hash_pass

@blueprint.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('home_blueprint.index'))
    form = ResetPasswordRequestForm()

    if 'reset_password' in request.form:
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        return redirect(url_for('authentication_blueprint.login'))

    elif request.method == 'GET':
        form.email.data = ''

    return render_template('accounts/emailpass.html',
                           msg='Введите Ваш email', form=form)

@blueprint.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home_blueprint.index'))
    user = Users.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('home_blueprint.index'))
    ResetPassForm = ResetPasswordForm()
    if 'reset_password' in request.form:
        if ResetPassForm.password.data==ResetPassForm.password2.data:
            user.set_password(ResetPassForm.password.data)
            db.session.commit()
            # flash('Your password has been reset.')
            return redirect(url_for('authentication_blueprint.login'))
        else :
            print('Пароль не совпадает')
            render_template( 'accounts/reset_passwordform.html',
                             msg='Пароль не совпадает',
                             success=False,
                             form=ResetPassForm)

    return render_template( 'accounts/reset_passwordform.html',
                            msg='Введите новый пароль 2 раза',
                            success=False,
                            form=ResetPassForm)

@blueprint.route('/')
def route_default():
    # print('Мы на /')
    return redirect(url_for('home_blueprint.index'))  #На главной странице логин не нужен
    # return redirect(url_for('authentication_blueprint.login'))

# Login & Registration

@blueprint.route("/github")
def login_github():
    """ Github login """
    if not github.authorized:
        return redirect(url_for("github.login"))

    res = github.get("/user")
    return redirect(url_for('home_blueprint.index'))

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = Users.query.filter_by(username=username).first()

        # Check the password
        if user and verify_pass(password, user.password):
            if not current_user.is_anonymous:
                logout_user()
            login_user(user, remember=True)
            # if not current_user.is_anonymous:
            #     current_user.username=username
            #     current_user.password=password

            return redirect(url_for('home_blueprint.main'))

        # Something (user or pass) is not ok
        return render_template('accounts/login.html',
                               msg='Неверный логин или пароль',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html',
                               form=login_form)
    return redirect(url_for('home_blueprint.main'))


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username = request.form['username']
        email = request.form['email']

        # Check username exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Пользователь уже существует',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Email уже существует',
                                   success=False,
                                   form=create_account_form)

        # else we can create the user
        # print(current_user.is_authenticated)
        user = PseudoUser(log_in=False)
        if user:
            db.session.execute(update(Users).where(Users.id == int(user.id)).\
                values(username=username, password=hash_pass(request.form['password']), email=email))
            db.session.flush()
            db.session.commit()
        # print(user)
        # if not current_user.is_authenticated:  #Пользователь не залогинен
        #     print('Создаем нового')
        #     user = Users(**request.form)
        #     db.session.add(user)
        #     db.session.flush()
        #     db.session.commit()
        # else:       #Пользователь залогинен как аноним
        #     user=PseudoUser()
        #     logout_user()
        #     print('Переименовываем')
        #     user.username = username
        #     user.password = request.form['password']
        #     user.email = email
        #     db.session.commit()
        #     # user=current_user
        #     print(user.username)

        #Добавляем так же все фильтры для всех категорий в True
        categories = Category.query.all()
        if not categories: #Если нет категорий - добавляем по умолчанию
            catsList= ['Хозяйственный набор', 'Аптечка хозяйственная', 'Аптечка тактическая', 'Защита', 'Подготовка']
            catPhotos = ['ownclothes.png', 'medics.png', 'firstaid.png', 'multicam.png', 'phisics.png']
            for catPhoto, category in zip(catPhotos, catsList):
                cat = Category(catname=category)
                db.session.add(cat)
                db.session.commit()
                photo = CategoryPhotos(category_id=cat.id, photo=catPhoto)
                db.session.add(photo)
                db.session.commit()
            categories = Category.query.all()

        #Обновляем фильтры категорий только если для данного пользователя их еще нет
        catFilters = UserCatFilters.query.filter(UserCatFilters.user==user.id).first()
        if not catFilters:
            for cat in categories:
                userFilter = UserCatFilters(user, cat)
                db.session.add(userFilter)
                db.session.commit()
        #Удаляем мусорных пользователей старше OLD_USERS_DELAY дней
        clearOldUsers(app.config['OLD_USERS_DELAY'])
        # Delete user from session
        logout_user()
        
        return render_template('accounts/register.html',
                               msg='Регистрация успешна.',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('accounts/register.html', form=create_account_form)

#Чистим базу от старых пользователей
def clearOldUsers(ddays=30):
    '''
    Удаляет всех псевдо пользователей с возрастом старше ddays дней
    :return:
    '''
    #Удалим всех пользователей без пароля старше месяца
    oldUsers=Users.query.filter((Users.password==None) & (Users.timestamp < datetime.utcnow()-timedelta(seconds=ddays))).all()
    for old in oldUsers:
        db.session.delete(old)
        try:
            db.session.commit()
        except:
            db.session.rollback()

@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))


# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500

