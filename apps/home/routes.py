# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, request, redirect, url_for, jsonify, send_file
from flask import send_from_directory, make_response
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from apps.home.forms import AddItemForm, EditItemForm, SettingsForm, AddArticleForm, EditArticleForm, AddPostForm
from sqlalchemy import func
from apps.authentication.models import Users
from apps import db, csrf
from apps.authentication.models import Category, ItemPhotos, Item, Activity, Comment, Article, \
    ArticlePhotos, UserCatFilters, Post
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import pandas as pd
from flask import current_app as app
import time
import uuid
from flask_ckeditor import upload_success, upload_fail
from math import ceil
import xlsxwriter
from pytube import YouTube
import requests
import re
# import bbcode

@blueprint.route('/index')
def index():
    return render_template('home/index.html', segment='index')

@blueprint.route('/robots.txt')
@blueprint.route('/sitemap.xml')
def static_from_root():
    print(app.config['SITEMAP_FILEPATH'], request.path[1:])
    return send_from_directory(app.config['SITEMAP_FILEPATH'], request.path[1:])

@blueprint.route('/settings.html', methods=['GET', 'POST'])
@login_required
def settings():

    settings_form = SettingsForm(request.form)
    if 'saveSettings' in request.form :
        setattr(current_user, 'first_name', settings_form.first_name.data)
        setattr(current_user, 'last_name', settings_form.last_name.data)
        setattr(current_user, 'burth_date', settings_form.burth_date.data)
        db.session.commit()
        return redirect(url_for('home_blueprint.main'))
    elif request.method == 'GET':
        settings_form.first_name.data = current_user.first_name
        settings_form.last_name.data = current_user.last_name
        settings_form.burth_date.data = current_user.burth_date

    return render_template('home/settings.html', segment='settings', form = settings_form)

@blueprint.route('/main.html', methods=['GET'])
# @login_required
def main():
    def makeSelectedButton(selectedState, haveItState, id, user, bDisabled):
        bLogged = 'False' if current_user.is_anonymous else 'True'
        if selectedState:
            result = '''<div class="form-switch" onclick=checkButtonsStatus()> <input class="form-check-input" type="checkbox" name="inList_''' + str(id) \
               + '''" id="inList_''' + str(id) + '" checked ' + bDisabled +''' onclick=changeSelected("inList_''' + str(id) + '''")> 
               <label class ="form-check-label" for ="inList_''' + str(id) + '''"> В списке </label></div>'''
        else:
            result =  '''<div class="form-switch" onclick=checkButtonsStatus()> <input class="form-check-input" type="checkbox" name="inList_''' + str(id) \
                   +  '''" id="inList_''' + str(id) + '" ' + bDisabled +''' onclick=changeSelected("inList_''' + str(id) + '''")>
                   <label class ="form-check-label" for ="inList_''' + str(id) + '''"> В списке </label></div>'''
        if haveItState:
            result = result + ''' <div class="form-switch" onclick=checkButtonsStatus()> <input class="form-check-input" type="checkbox" name="idHaveIt_''' + str(id) \
                     + '''" id="idHaveIt_''' + str(id) + '" checked ' + bDisabled +''' onclick=changeSelected("idHaveIt_''' + str(id) + '''")>
                     <label class ="form-check-label" for ="idHaveIt_''' + str(id) + '''"> Уже есть </label></div>'''
        else:
            result = result + '''<div class="form-switch" onclick=checkButtonsStatus()> <input class="form-check-input" type="checkbox" name="idHaveIt_''' + str(id) \
                     + '''" id="idHaveIt_''' + str(id) + '" ' + bDisabled +''' onclick=changeSelected("idHaveIt_''' + str(id) + '''")>
                     <label class ="form-check-label" for ="idHaveIt_''' + str(id) + '''"> Уже есть </label></div>'''
        return result

    def makeFilter(id, label, value, bDisabled):
        result = '''<div class="form-switch" onclick=checkButtonsStatus()> <input class="form-check-input" type="checkbox" name="mainFilter_''' + str(id) \
                 + '" id="mainFilter_' + str(id) + '" ' + value + bDisabled +'onclick=changeFilter("mainFilter_' + str(id) + \
        '")><label class ="form-check-label mx-2" for ="mainFilter_' + str(id) + '">' + label + '</label></div>'
        return result

    def makeLink(id, name):
        return '<a href = "' + url_for('home_blueprint.edititem', item_id=str(id)) + \
               '">' + str(name) + '</a>'
    def makePhoto(link, alt):
        return '<img itemprop="image" src="' + str(link) +'" alt="'+ str(alt) +'" src=' + str(link) + ' width="100px" height="100px" class="img-fluid rounded-0 alt="' + str(alt) + '">'

    page = request.args.get('page', 1, type=int)

    #Данные
    if not current_user.is_anonymous:
        dfItems = pd.read_sql('''SELECT  itm.id, itm.name, itm.price, itm.user_added, ctg.catname, act.inList, act.haveIt,
                (SELECT itf.photo FROM ItemPhotos itf WHERE itf.item_id = itm.id ORDER BY Photo ASC LIMIT 1) AS Photo
                FROM Items itm LEFT JOIN Categories ctg ON (ctg.id = itm.category)
                LEFT JOIN Activity act ON (act.item_id = itm.id) 
                WHERE act.user_id=''' + str(current_user.id) +
                              ' ORDER BY itm.update_date DESC;', db.session.bind)
        bDisabled = ''
    #Собираем строку фильтров
        catFiltersquery = db.session.query(UserCatFilters.query.with_entities(Category.id, Category.catname, UserCatFilters.value) \
            .join(Category).filter(UserCatFilters.user == current_user.id).order_by(Category.id).subquery())
        dfFilters = pd.read_sql(catFiltersquery.statement, db.session.bind)
    else:
        dfItems = pd.read_sql('''SELECT  itm.id, itm.name, itm.price, itm.user_added, ctg.catname, '1' AS inList, '1' AS haveIt,
                (SELECT itf.photo FROM ItemPhotos itf WHERE itf.item_id = itm.id ORDER BY Photo ASC LIMIT 1) AS Photo
                FROM Items itm LEFT JOIN Categories ctg ON (ctg.id = itm.category) ORDER BY itm.update_date DESC;''', db.session.bind)
        bDisabled = ' Disabled '
        # Собираем строку фильтров без user, всем True
        catFiltersquery = db.session.query(Category.query.with_entities(Category.id, Category.catname) \
            .order_by(Category.id).subquery())
        dfFilters = pd.read_sql(catFiltersquery.statement, db.session.bind)
        dfFilters['value'] = True
    #преобразуем catname в html
    dfFilters['value'] = dfFilters['value'].apply(lambda x: ' checked ' if x else '')
    # print(dfFilters.head())
    if not dfFilters.empty:
        dfFilters['catname'] = dfFilters.apply(lambda x: makeFilter(x.id, x.catname, x.value, bDisabled), axis=1)
    dfFilters.drop(columns=['id', 'value'], inplace=True)

    #фильтруем Items по выбранным фильтрам, если без пользователя - показываем все предметы
    if not current_user.is_anonymous:
        categoryFiltersquery = db.session.query(UserCatFilters.query.with_entities(Category.id.label('cat_id'), Category.catname, UserCatFilters.value) \
            .join(Category).filter(UserCatFilters.user == current_user.id, UserCatFilters.value==True).subquery())
        dfCatFilters = pd.read_sql(categoryFiltersquery.statement, db.session.bind)
        dfItems = dfItems.merge(dfCatFilters[['catname', 'value']], on = 'catname', how='left')
        dfItems = dfItems.loc[dfItems['value']==True]

    #Из Activity рассчитаем среднюю оценку
    query = db.session.query(Activity.query.with_entities(Activity.item_id, func.avg(Activity.rating)).\
            group_by(Activity.item_id).subquery())
    dfRating = pd.read_sql(query.statement, db.session.bind)
    dfRating.rename(columns={'item_id':'id', 'avg_1':'rating'}, inplace=True)
    dfRating.dropna(subset=['rating'], inplace=True)
    if not dfRating.empty:
        dfRating['rating'] = dfRating['rating'].round(1)
    dfItems = dfItems.merge(dfRating, on='id', how='left')

    #Посчитаем стоимость предметов в списке
    dTotalSomme = dfItems.loc[dfItems['inList']==True]['price'].sum()
    # print(dTotalSomme)
    #Теперь сколько из списка осталось докупить
    dSommeToBuy = dfItems.loc[(dfItems['inList']==True) & (dfItems['haveIt']==False)]['price'].sum()
    # print(dSommeToBuy)

    #выбираем только записи нужной страницы
    pagesCount = ceil(len(dfItems.index)/app.config['ITEMS_PER_PAGE'])
    dfItems = dfItems[app.config['ITEMS_PER_PAGE'] * (page-1):app.config['ITEMS_PER_PAGE'] * (page)]

    # print(dfRating)
    # print(dfItems.head())
    dfItems['selected'] = dfItems['inList']
    dfItems['selected'] = dfItems.apply(lambda x: makeSelectedButton(x.selected, x.haveIt, x.id, x.user_added, bDisabled), axis=1)

    dfItems = dfItems[['Photo', 'id', 'selected', 'catname', 'name', 'rating', 'price']]
    dfItems['Photo'] = dfItems['Photo'].apply( lambda x: url_for('static',
                    filename=os.path.join(app.config['PHOTOS_FOLDER'], x).replace('\\','/')) if x else None)
    dfItems['Photo'] = dfItems.apply( lambda x: makePhoto(x['Photo'], x['name']), axis=1)
    dfItems['Photo'] = dfItems.apply(lambda x: makeLink(x['id'], x['Photo']), axis=1)
    dfItems['name'] = dfItems.apply(lambda x: makeLink(x['id'], x['name']), axis=1)
    dfItems['id'] = dfItems['id'].apply \
        (lambda x: '<a href = "' + url_for('home_blueprint.edititem', item_id=str(x)) +
                   '">' + str(x) + '</a>')
    itemscount=len(dfItems.index)


    return render_template('home/main.html', segment='main', row_data=list(dfItems.values.tolist()),
                           currPage=page, pagesCount=pagesCount, categories=list(dfFilters['catname']),
                           dSommeInList=round(dTotalSomme), dSommeToBuy=round(dSommeToBuy), itemscount=itemscount) #


@blueprint.route('/checkStatus', methods=['POST'])
def checkStatus():
    return jsonify({'logged': not current_user.is_anonymous, 'link': url_for('authentication_blueprint.login'),
                    'register': url_for('authentication_blueprint.register')})

@blueprint.route('/additem.html', methods=['GET', 'POST'])
@login_required
def additem():

    categories = Category.query.with_entities(Category.id, Category.catname).all()
    categories.insert(0, (-1, 'Выберите категорию'))
    additem_form = AddItemForm(request.form)
    additem_form.category.choices = categories
    # print(additem_form.validate_on_submit())
    if 'addnewitem' in request.form :
        argslst = dict(request.form)
        # print(argslst)
        argslst = {key: argslst[key]  for key in argslst if key not in ['addnewitem', 'photos']}
        argslst['user_added'] = current_user.id
        # print(argslst)
        # read form data
        item = Item(**argslst)
        if additem_form.video_link.data != '':
            if 'youtube' in additem_form.video_link.data:
                item.video_thumbnail = 'https://img.youtube.com/vi/' + additem_form.video_link.data.split('=')[
                    1] + '/0.jpg'
            else:
                item.video_thumbnail = 'https://img.youtube.com/vi/' + additem_form.video_link.data.split('/')[
                    3] + '/0.jpg'
        db.session.add(item)
        for file in request.files.getlist('photos'):  #additem_form.photos.data
            photo = secure_filename(file.filename)
            if photo:
                new_filename = current_user.username + "_" + datetime.today().strftime('%Y_%m_%d_%H_%M_%S') + "_" + photo
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                newphoto = ItemPhotos(Item=item, photo=new_filename)
                db.session.add(newphoto)

        # print(argslst)

        inList = False if 'inList' not in argslst else True if argslst['inList'] == 'y' else False
        haveIt = False if 'haveIt' not in argslst else True if argslst['haveIt'] == 'y' else False
        rating = argslst['rating'] if 'rating' in argslst else None

        newactivity = Activity(Item=item, User=current_user, inList=inList,
                               haveIt=haveIt, rating=rating)
        db.session.add(newactivity)
        db.session.commit()
        return redirect(url_for('home_blueprint.main'))

    return render_template('home/additem.html', segment='additem', form = additem_form)

@blueprint.route('/edititem.html/<item_id>', methods=['GET', 'POST'])
# @login_required
def edititem(item_id):
    def createPhotoLink(id, photo, alt):
        return '''<figure class="figure"> 
                <img itemprop="image" id=photo_''' + str(id) + ' src="'+ url_for('static',
                filename=os.path.join(app.config['PHOTOS_FOLDER'], photo).replace('\\','/'))\
               + '''"  width="250px" height="250px" class="img-fluid rounded-0" alt="''' + alt.replace('"','in') + '''">
               </figure>'''

    categories = Category.query.with_entities(Category.id, Category.catname).all()
    categories.insert(0, (-1, 'Выберите категорию'))
    edititem_form = EditItemForm(request.form)
    edititem_form.category.choices = categories

    # print(additem_form.validate_on_submit())
    if 'Edititem' in request.form:
        argslst = dict(request.form)
        # print(argslst, True if 'inList' in argslst else False)
        #Чужому Item можно редактировать оценку, добавлять фото, добавлять в свой список, отмечать наличие
        item = Item.query.filter(Item.id == item_id).first()
        if item.user_added == current_user.id: #Только создавший пользователь может обновлять Item
            item.category = edititem_form.category.data
            item.name = edititem_form.name.data
            item.description = edititem_form.description.data
            item.price = edititem_form.price.data
            item.video_link = edititem_form.video_link.data
            if edititem_form.video_link.data != '':
                if 'youtube' in edititem_form.video_link.data:
                    item.video_thumbnail = 'https://img.youtube.com/vi/' + edititem_form.video_link.data.split('=')[
                        1] + '/0.jpg'
                else:
                    item.video_thumbnail = 'https://img.youtube.com/vi/' + edititem_form.video_link.data.split('/')[
                        3] + '/0.jpg'
            for file in request.files.getlist('photos'):  #additem_form.photos.data
                photo = secure_filename(file.filename)
                if photo:
                    new_filename = current_user.username + "_" + datetime.today().strftime('%Y_%m_%d_%H_%M_%S') + "_" + photo
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                    newphoto = ItemPhotos(Item=item, photo=new_filename)
                    db.session.add(newphoto)
        editActivity = Activity.query.filter(Activity.item_id == item_id, Activity.user_id==current_user.id).first()

        setattr(editActivity, 'rating', argslst['rating'] if 'rating' in argslst else 0)
        setattr(editActivity, 'inList', True if 'inList' in argslst else False)
        setattr(editActivity, 'haveIt', True if 'haveIt' in argslst else False)

        db.session.commit()
        return redirect(url_for('home_blueprint.main'))
    elif 'Delete' in request.form:  #Удаляем item и связанные Activity

        db.session.delete(Item.query.get(item_id))
        db.session.commit()
        return redirect(url_for('home_blueprint.main'))
    elif 'Cancel' in request.form:
        return redirect(url_for('home_blueprint.main'))

    elif request.method == 'GET':
        # Все поля может редактировать только создатель Item
        changeRating=True
        owner=False
        user = None if current_user.is_anonymous else current_user
        rating=None
        # Все поля может редактировать только создатель Item
        if not current_user.is_anonymous:
            values = db.session.query(Item, Category, Activity).with_entities(
                Item.id, Item.user_added, Item.name,  Item.description, Item.price, Item.video_link,
                Item.category, Category.catname, Activity.inList, Activity.haveIt,
                Activity.rating).join(Category, Activity).filter(Item.id == item_id, Activity.user_id==current_user.id).first()
            owner = True if values['user_added'] == current_user.id else False  # Редактирует создатель Item
            # print(query.statement)
            if not values: #На этого пользователя нет записи с рейтингом - другой делал товар
                currItem = Item.query.filter(Item.id == item_id).first()
                newactivity = Activity(Item=currItem, User=current_user, inList=False,
                                       haveIt=False)
                db.session.add(newactivity)
                db.session.commit()
                values = db.session.query(Item, Category, Activity).with_entities(
                    Item.id, Item.name, Item.description, Item.price, Item.video_link,
                    Item.category, Category.catname, Activity.inList, Activity.haveIt,
                    Activity.rating).join(Category, Activity).filter(Item.id == item_id,
                                                                     Activity.user_id == current_user.id).first()
            edititem_form.inList.data = values['inList']
            edititem_form.haveIt.data = values['haveIt']
            rating = values['rating']
            # print('Мы здесь', values['rating'], edititem_form.rating.data)
        else:  #аноним
            # values = db.session.query(Item, Category).with_entities(
            #     Item.id, Item.name, Item.description, Item.price, Item.video_link,
            # Item.category, Category.catname).join(Category) \
            #     .filter(Item.id == item_id).first()
            values = db.session.query(Item, Category, Activity).with_entities(
                Item.id, Item.name, Item.description, Item.price, Item.video_link,
                Item.category, Category.catname, Activity.inList, Activity.haveIt,
                Activity.rating).join(Category, Activity).filter(Item.id == item_id).first()
            rating = values['rating']
            changeRating = False

        values = values._mapping
        # print(values)
        edititem_form.category.default = values['category']
        edititem_form.process()
        edititem_form.name.data = values['name']
        edititem_form.rating.data = rating if rating else 0

        edititem_form.description.data = values['description']
        edititem_form.price.data = values['price']
        edititem_form.video_link.data = values['video_link']
        # print(edititem_form.price.data)

        currItem=Item.query.get(item_id)
        query = db.session.query(ItemPhotos).filter(ItemPhotos.item_id == item_id)
        dfPhotos = pd.read_sql(query.statement, query.session.bind)
        if not dfPhotos.empty:
            # print(dfPhotos)
            dfPhotos['photo'] = dfPhotos.apply(lambda x: createPhotoLink(x.id, x.photo, currItem.name), axis=1)

        #Комментарии
        # newComment = currItem.add_emptycomment(current_user)
        comments = currItem.followed_comments(user).all()
        # print(user, currItem, comments)
        dfComments = pd.DataFrame.from_records(comments, index='id', columns=['id', 'user', 'text'])
        # print(dfComments)
        # выбираем только комментарии нужной страницы
        page = request.args.get('page', 1, type=int)
        pagesCount = ceil(len(dfComments.index) / app.config['COMMENTS_PER_PAGE'])
        dfComments = dfComments[app.config['COMMENTS_PER_PAGE'] * (page - 1):app.config['COMMENTS_PER_PAGE'] * (page)]

        video_link = None
        if currItem.video_link:
            if 'youtube' in currItem.video_link:
                video_link = currItem.video_link.split('=')[1] if  '=' in currItem.video_link else None
            else:
                video_link = currItem.video_link.split('/')[3] if  '/' in currItem.video_link else None

        return render_template('home/edititem.html', segment='edititem', form=edititem_form,
                               photos=list(dfPhotos['photo'].values.tolist()),
                               comments_data=list(dfComments.values.tolist()), owner=owner, changeRating=changeRating,
                               currPage=page, pagesCount=pagesCount, item_id=item_id, video_link=video_link)


#Добавление новой статьи
@blueprint.route('/addarticle.html', methods=['GET', 'POST'])
@login_required
def addarticle():
    article_form = AddArticleForm(request.form)
    if 'addarticle' in request.form:
        argslst = dict(request.form)
        # print(argslst)
        argslst = {key: argslst[key]  for key in argslst if key not in ['addarticle']}
        argslst['user_added'] = current_user.id
        article = Article(**argslst)
        if article_form.video_link.data != '':
            if 'youtube' in article_form.video_link.data:
                article.video_thumbnail = 'https://img.youtube.com/vi/' + article_form.video_link.data.split('=')[
                    1] + '/0.jpg'
                video_id =article_form.video_link.data.split('=')[1]
            else:
                article.video_thumbnail = 'https://img.youtube.com/vi/' + article_form.video_link.data.split('/')[
                    3] + '/0.jpg'
                video_id = article_form.video_link.data.split('/')[3]
            #Заполним так же мета информацию по видео
            yt = YouTube('https://www.youtube.com/watch?v=' +video_id )
            article.video_author = yt.author
            article.video_description = yt.description
            article.video_name = yt.title
            article.video_uploadDate = yt.publish_date.strftime("%Y-%m-%d")
            article.video_ageRestricted = yt.age_restricted
            article.video_rating = yt.rating
            article.video_views = yt.views
            article.video_keywords = ', '.join(yt.keywords)
            # print(article.video_keywords)
            hours = int(yt.length / 3600)
            minutes = int((yt.length - hours * 3660) / 60)
            seconds = int(yt.length - hours * 3600 - minutes * 60)
            article.video_duration = 'PT' + str(hours) + 'H' + str(minutes) +'M' + str(seconds) + 'S'
            #количество комментариев
            params = {
                'part': 'statistics',
                'id': video_id,
                'key': app.config['YT_APIKEY']
            }
            d = requests.get('https://www.googleapis.com/youtube/v3/videos', params=params).json()
            article.video_commentsCount = d['items'][0]['statistics']['commentCount']
            article.video_likes = d['items'][0]['statistics']['likeCount']

        db.session.add(article)
        for file in request.files.getlist('photos'):  #additem_form.photos.data
            photo = secure_filename(file.filename)
            if photo:
                new_filename = current_user.username + "_" + datetime.today().strftime('%Y_%m_%d_%H_%M_%S') + "_" + photo
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                newphoto = ArticlePhotos(Article=article, photo=new_filename)
                db.session.add(newphoto)

        rating = argslst['rating'] if 'rating' in argslst else None
        # rating = 0 if 'rating' not in argslst else argslst['rating']
        newactivity = Activity(Article=article, User=current_user, rating=rating)
        db.session.add(newactivity)
        db.session.commit()
        return redirect(url_for('home_blueprint.articlesMain'))
    elif 'Cancel' in request.form:
        return redirect(url_for('home_blueprint.articlesMain'))
    elif request.method=='GET':

        return render_template('home/addarticle.html', segment='addarticle', form=article_form)


@blueprint.route('/editarticle.html/<article_id>', methods=['GET', 'POST'])
# @login_required
def editarticle(article_id):
    def createPhotoLink(id, photo, alt):
        return '''<figure class="figure"> 
                <img id=photo_''' + str(id) + ' src="'+ url_for('static',
                filename=os.path.join(app.config['PHOTOS_FOLDER'], photo).replace('\\','/'))\
               + '''"  width="150px" height="150px" class="img-fluid rounded-0 alt="''' + alt + '"></figure>'

    article_form = EditArticleForm(request.form)
    if 'editarticle' in request.form:
        argslst = dict(request.form)
        # Чужому Item можно редактировать оценку, добавлять фото, добавлять в свой список, отмечать наличие
        article = Article.query.get(article_id)
        if article.user_added == current_user.id:
            article.title = article_form.title.data
            article.video_link = article_form.video_link.data
            article.body = article_form.body.data
            # print('Длина текста =', len(article_form.body.data))
            if article_form.video_link.data !='':
                if 'youtube' in article_form.video_link.data:
                    article.video_thumbnail = 'https://img.youtube.com/vi/' + article_form.video_link.data.split('=')[
                        1] + '/0.jpg'
                else:
                    article.video_thumbnail = 'https://img.youtube.com/vi/' + article_form.video_link.data.split('/')[
                        3] + '/0.jpg'

            for file in request.files.getlist('photos'):  # additem_form.photos.data
                photo = secure_filename(file.filename)
                if photo:
                    new_filename = current_user.username + "_" + datetime.today().strftime(
                        '%Y_%m_%d_%H_%M_%S') + "_" + photo
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                    newphoto = ArticlePhotos(Article=article, photo=new_filename)
                    db.session.add(newphoto)
        editActivity = Activity.query.filter(Activity.article_id == article_id, Activity.user_id == current_user.id).first()
        # rating = 0 if 'rating' not in argslst else argslst['rating']
        rating = argslst['rating'] if 'rating' in argslst else None
        if rating:
            setattr(editActivity, 'rating', rating)
        db.session.commit()
        return redirect(url_for('home_blueprint.articlesMain'))
    elif 'Delete' in request.form:  #Удаляем item и связанные Activity
        db.session.delete(Article.query.get(article_id))
        db.session.commit()
        return redirect(url_for('home_blueprint.articlesMain'))

    elif request.method == 'GET':
        currArticle = Article.query.get(article_id)
        user = None if current_user.is_anonymous else current_user
        owner = False

        changeRating = True
        # Все поля может редактировать только создатель Item
        if not current_user.is_anonymous:
            owner = True if currArticle.user_added == current_user.id else False
            values = db.session.query(Article, Activity).with_entities(
                Article.id, Article.user_added, Article.title, Article.body, Article.video_link,
                Activity.rating).join(Activity).filter(Article.id == article_id,
                                                                 Activity.user_id == current_user.id).first()

            if not values:  # На этого пользователя нет записи с рейтингом - другой делал товар
                newactivity = Activity(Article=currArticle, User=current_user)
                db.session.add(newactivity)
                db.session.commit()
                values = db.session.query(Article, Activity).with_entities(
                    Article.id, Article.title, Article.body, Article.video_link,
                    Activity.rating).join(Activity).filter(Article.id == article_id,
                                                                     Activity.user_id == current_user.id).first()
            article_form.rating.data = values['rating']
        else:   #пльзователь не залогинен - не будет возможности оценки
            values = db.session.query(Article).with_entities(
                Article.id, Article.title, Article.body, Article.video_link).join(Activity)\
                .filter(Article.id == article_id).first()
            changeRating = False

        # values = values._mapping

        article_form.title.data = currArticle.title
        article_form.video_link.data = currArticle.video_link
        article_form.body.data = currArticle.body
        # article_form.video_thumbnail.data = currArticle.video_thumbnail

        currArticle=Article.query.get(article_id)
        query = db.session.query(ArticlePhotos).filter(ArticlePhotos.article_id == article_id)
        dfPhotos = pd.read_sql(query.statement, query.session.bind)
        if not dfPhotos.empty:
            dfPhotos['photo'] = dfPhotos.apply(lambda x: createPhotoLink(x.id, x.photo, currArticle.title), axis=1)

        # Комментарии
        currArticle = Article.query.get(article_id)
        comments = currArticle.followed_comments(user).all()
        dfComments = pd.DataFrame.from_records(comments, index='id', columns=['id', 'user', 'text'])

        # выбираем только комментарии нужной страницы
        page = request.args.get('page', 1, type=int)
        # print(page)
        if dfComments.empty:
            pagesCount = 1
        else:
            pagesCount = ceil(len(dfComments.index) / app.config['COMMENTS_PER_PAGE'])
        dfComments = dfComments[app.config['COMMENTS_PER_PAGE'] * (page - 1):app.config['COMMENTS_PER_PAGE'] * (page)]

        video_link = None
        articleStruct = None
        if currArticle.video_link:
            if 'youtube' in currArticle.video_link:
                video_link = currArticle.video_link.split('=')[1] if '=' in currArticle.video_link else None
            else:
                video_link = currArticle.video_link.split('/')[3] if '/' in currArticle.video_link else None
            articleStruct = {'video_thumbnail':currArticle.video_thumbnail,
                             'video_author' :currArticle.video_author,
                             'video_description' : currArticle.video_description,
                            'video_name' : currArticle.video_name,
                            'video_uploadDate' : currArticle.video_uploadDate,
                            'video_ageRestricted' : currArticle.video_ageRestricted,
                            'video_duration' : currArticle.video_duration,
                            'video_likes' :  currArticle.video_likes,
                            'video_views' : currArticle.video_views,
                            'video_commentsCount': currArticle.video_commentsCount,
                            'video_keywords': currArticle.video_keywords}
            # print(articleStruct)
        return render_template('home/editarticle.html', segment='editarticle', form=article_form,
                               photos=list(dfPhotos['photo'].values.tolist()),
                               comments_data=list(dfComments.values.tolist()), owner=owner, changeRating=changeRating,
                               currPage=page, pagesCount=pagesCount, article_id=article_id, video_link =video_link,
                               articleStruct=articleStruct)

    return render_template('home/editarticle.html', segment='editarticle', form=article_form)


#список категорий топиков
@blueprint.route('/postsMain.html', methods=['GET'])
# @login_required
def postsMain():

    def makeLink(id, name):
        return '<a href = "' + url_for('home_blueprint.postsTopics', category_id=str(id)) + \
               '">' + str(name) + '</a>'
    def CategoriesPhoto(src, alt):
        if src:
            return '<img src=' + src + ' width="250px" height="250px" class="img-fluid rounded-0 alt="' + alt + '">'
        else:
            return '<img src="" width="250px" height="250px" class="img-fluid rounded-0 alt="' + alt + '">'

    # page = request.args.get('page', 1, type=int)
    dfCategories = pd.read_sql('''SELECT  Categories.id, Categories.catname,
            (SELECT ctf.photo FROM CategoryPhotos ctf WHERE ctf.category_id = Categories.id ORDER BY ctf.id ASC LIMIT 1) AS Photo
            FROM Categories  ORDER BY Categories.id;''', db.session.bind)

    #Из Activity рассчитаем количество постов по категориям
    query = db.session.query(Post.query.with_entities(Post.category_id, func.count()).\
            group_by(Post.category_id).subquery())
    dfPosts = pd.read_sql(query.statement, db.session.bind)
    dfPosts.rename(columns={'category_id':'id', 'count_1':'posts'}, inplace=True)
    if len(dfPosts.loc[~dfPosts['id'].isna()]) >0:
        dfCategories = dfCategories.merge(dfPosts, on='id', how='left')
    else:
        dfCategories['posts'] = 0
    dfCategories['posts'].fillna(0, inplace=True)
    dfCategories['posts']=dfCategories['posts'].astype(int)
    dfCategories['Photo'] = dfCategories['Photo'].apply( lambda x: url_for('static',
                    filename=os.path.join(app.config['ILLUSTRATIONS_FOLDER'], x).replace('\\','/')) if x else None)
    dfCategories['Photo'] = dfCategories.apply( lambda x: CategoriesPhoto(x['Photo'], x.catname), axis=1)
    dfCategories['catname'] = dfCategories.apply(lambda x: makeLink(x['id'], x['catname']), axis=1)

    firstquery = db.session.query(
        Post.category_id, Post.topic_label). \
        group_by(Post.category_id, Post.topic_label).subquery()
    mainQuery = db.session.query(firstquery.c.category_id, func.count(firstquery.c.topic_label)).\
        group_by(firstquery.c.category_id)
    dfTopics = pd.read_sql(mainQuery.statement, db.session.bind)
    dfTopics.rename(columns={'category_id':'id', 'count_1':'topics'}, inplace=True)
    dfCategories = dfCategories.merge(dfTopics, on='id', how='left')
    dfCategories['topics'].fillna(0, inplace=True)
    dfCategories['topics']=dfCategories['topics'].astype(int)
    # print(dfPosts.head(10))

    #Теперь найдем последний пост по каждому топику
    query = db.session.query(Post.query.with_entities(Post.topic_label, Post.category_id, Users.username, func.max(Post.timestamp)).\
                             join(Users).filter(Post.parentPost == None).group_by(Post.category_id).subquery())
    dfLastPosts=pd.read_sql(query.statement, db.session.bind)
    # dfLastPosts['body']=dfLastPosts['body'].apply(lambda x: x[:50] +'...')

    dfLastPosts['body'] = dfLastPosts['topic_label'].apply(lambda x: ''.join([re.sub(r'\<[^>]*\>', '', x)[:50], '...']))
    dfLastPosts.rename(columns={'category_id':'id', 'username':'lastModifiedBy', 'max_1':'lastTime', 'body':'lastPostBody'}, inplace=True)
    if not dfCategories.empty:
        dfCategories = dfCategories.merge(dfLastPosts, on='id', how='left')
    dfCategories[['lastModifiedBy', 'lastTime']].fillna('-', inplace=True)
    dfCategories['lastPostBody'] = dfCategories['lastPostBody'].str.replace('&nbsp;', '')

    dfCategories = dfCategories[['id', 'Photo', 'catname', 'topics', 'posts', 'lastModifiedBy', 'lastTime', 'lastPostBody']]
    return render_template('home/postsMain.html', segment='postsMain', row_data=list(dfCategories.values.tolist()))


#список категорий топиков
@blueprint.route('/postsTopics.html/<category_id>', methods=['GET'])
def postsTopics(category_id):
    def makeLink(id, name):
        return '<a href = "' + url_for('home_blueprint.forumPage', category_id=str(id)) + \
               '">' + str(name) + '</a>'
    def CategoriesPhoto(src, alt):
        return '<img src=' + src if src else '' + ' width="250px" height="250px" class="img-fluid rounded-0 alt="' + alt + '">'

    currCat = Category.query.get(category_id)

    query = db.session.query(Post.query.with_entities(Post.topic_label, Post.category_id, Users.username).join(Users).\
            filter(Post.category_id==category_id).group_by(Post.topic_label).order_by(Post.timestamp).subquery())
    dfTopics = pd.read_sql(query.statement, db.session.bind)
    #рассчитаем количество постов по топикам
    query = db.session.query(Post.query.with_entities(Post.topic_label, func.count()).filter(Post.category_id==category_id).\
            group_by(Post.topic_label).subquery())
    dfPosts = pd.read_sql(query.statement, db.session.bind)
    dfPosts.rename(columns={'count_1':'posts'}, inplace=True)
    if len(dfPosts.loc[~dfPosts['topic_label'].isna()]) >0:
        dfTopics = dfTopics.merge(dfPosts, on='topic_label', how='left')
    else:
        dfTopics['posts'] = 0
    dfTopics['posts'].fillna(0, inplace=True)
    dfTopics['posts']=dfTopics['posts'].astype(int)

    #Теперь найдем последний пост по каждому топику
    query = db.session.query(Post.query.with_entities(Post.body, Post.topic_label, Users.username, func.max(Post.timestamp)).\
                             join(Users).filter(Post.category_id==category_id).group_by(Post.topic_label).subquery())
    dfLastPosts=pd.read_sql(query.statement, db.session.bind)
    dfLastPosts['body']=dfLastPosts['body'].apply(lambda x: ''.join([re.sub(r'\<[^>]*\>', '', x)[:50], '...']))
    dfLastPosts.rename(columns={'username':'lastModifiedBy', 'max_1':'last'
                                                                     'Time', 'body':'lastPostBody'}, inplace=True)
    if len(dfPosts.loc[~dfPosts['topic_label'].isna()]) >0:
        dfTopics = dfTopics.merge(dfLastPosts, on='topic_label', how='left')
    #Теперь найдем количество просмотров - в первом посте с этим топиком, без родителей
    query = db.session.query(Post.query.with_entities(Post.id, Post.topic_label, Post.views)\
                             .filter((Post.category_id==category_id) & (Post.parentPost == None)).subquery())
    dfPostViews=pd.read_sql(query.statement, db.session.bind)
    # print(dfPostViews)
    if len(dfPosts.loc[~dfPosts['topic_label'].isna()]) >0:
        dfTopics = dfTopics.merge(dfPostViews, on='topic_label', how='left')
    # print(dfTopics)
    if not dfTopics.empty:
        dfTopics['views'].fillna(0, inplace=True)
        dfTopics['views'] = dfTopics['views'].round(0).astype(int)
        dfTopics['lastPostBody'] = dfTopics['lastPostBody'].str.replace('&nbsp;', '')
        # print(dfTopics['lastPostBody'])
        dfTopics = dfTopics[['topic_label', 'username', 'posts', 'lastModifiedBy', 'lastTime', 'lastPostBody', 'views', 'id']]
    # print('Topics = ', dfTopics)

    return render_template('home/postsTopics.html', segment='postsTopics', row_data=list(dfTopics.values.tolist()),
                           category_id=category_id, catname=currCat.catname, )

#Просмотр поста по id и всех связанных
@blueprint.route('/forumPage.html/<category_id>/<post_id>', methods=['GET', 'POST'])
@login_required
def forumPage(category_id, post_id):

    if request.method=='GET':
        #получим топик и по нему заберем все субтопики
        # print(post_id)
        currPost = Post.query.get(post_id)

        currPost.views =1 if not currPost.views  else currPost.views +1
        db.session.commit()
        topic_label = currPost.topic_label
        query = db.session.query(Post).with_entities(Post.id, Users.username, Users.avatar_photo, Post.timestamp, Post.body,
                            Post.parentPost, Post.sourcebody, Users.id.label('user_id')).join(Users).\
            filter((Post.topic_label == topic_label) & (Post.category_id==category_id)).order_by(Post.timestamp)
        dfPosts = pd.read_sql(query.statement, query.session.bind)
        dfPosts['avatar_photo'] = dfPosts['avatar_photo'].apply(lambda x: url_for('static', filename=x))
        dfPosts['child'] = False
        dfPosts.loc[~dfPosts['parentPost'].isna(), 'child'] = True
        dfPosts['body']=dfPosts['body'].str.replace('class="quote"', 'class="blockquote"')
        dfPosts['postOwner'] = dfPosts['user_id'].apply(lambda x: x==current_user.id)
        # dfPosts['body'] = dfPosts['body'].apply(lambda x: bbcode.render_html(x))
        # print(dfPosts.head())
        dfPosts = dfPosts [['username', 'avatar_photo', 'timestamp', 'body', 'child', 'id', 'postOwner']]
#         print(dfPosts.head())
        catname = Category.query.get(currPost.category_id).catname

        return render_template('home/forumPage.html', segment='forumPage', row_data=list(dfPosts.values.tolist()), topic_label=topic_label,
                               category_id=category_id, post_id=post_id, catname=catname)

#Добавление новой статьи
@blueprint.route('/addPost.html/<category_id>/<post_id>', methods=['GET', 'POST'])
@login_required
def addPost(category_id=None, post_id=None):
    post_form = AddPostForm(request.form)
    if 'addPost' in request.form:
        argslst = dict(request.form)
        argslst = {key: argslst[key]  for key in argslst if key not in ['addPost']}
        argslst['user_added'] = current_user.id
        argslst['category_id'] = category_id
        post = Post(**argslst)
        # print(argslst)
        newParent = Post.query.filter(Post.topic_label==post_form.title.data).all()
        if post_id != '-1':
            parentPost=Post.query.get(post_id)
            post.category_id=parentPost.category_id
            if len(newParent)>0:  #есть уже такой топик
                post.parentPost = post_id
            else:
                post.parentPost = None

        post.topic_label= post_form.title.data
        db.session.add(post)
        db.session.commit()
        if post_id !='-1':
            return redirect(url_for('home_blueprint.postsTopics', category_id=parentPost.category_id))
        else:
            return redirect(url_for('home_blueprint.postsMain'))
    elif 'Cancel' in request.form:
        parentPost = Post.query.get(post_id)

        return redirect(url_for('home_blueprint.postsTopics', category_id=parentPost.category_id))
    elif request.method=='GET':
        # print(app.config['CKEDITOR_EXTRA_PLUGINS'])
        if post_id != '-1':
            post_form.post_id.data=post_id
            parentPost= Post.query.get(post_id)
            post_form.title.data = parentPost.topic_label
        return render_template('home/addPost.html', segment='postsMain', form=post_form, category_id=category_id, post_id=post_id)

#Добавление новой статьи
@blueprint.route('/editPost.html/<category_id>/<post_id>', methods=['GET', 'POST'])
@login_required
def editPost(category_id=None, post_id=None):
    post_form = AddPostForm(request.form)
    if 'addPost' in request.form:
        argslst = dict(request.form)
        argslst['user_added'] = current_user.id
        argslst['category_id'] = category_id
        if post_id != '-1':
            post = Post.query.get(post_id)
            post.body = argslst['body']
            db.session.commit()
            #Если это родительский пост то можно менять и топик - тогда у всех детей!
            if not post.parentPost:
                post.topic_label=post_form.title.data
                childs = Post.query.filter(Post.parentPost==post.id).all()
                for childPost in childs:
                    childPost.topic_label=post_form.title.data
                db.session.commit()
            return redirect(url_for('home_blueprint.postsTopics', category_id=post.category_id))
        else:
            return redirect(url_for('home_blueprint.postsMain'))
    elif 'Cancel' in request.form:
        parentPost = Post.query.get(post_id)
        return redirect(url_for('home_blueprint.postsTopics', category_id=parentPost.category_id))
    elif request.method=='GET':
        if post_id != '-1':

            post_form.post_id.data=post_id
            currPost= Post.query.get(post_id)
            post_form.title.data = currPost.topic_label
            post_form.body.data = currPost.body
        return render_template('home/editPost.html', segment='postsMain', form=post_form, category_id=category_id, post_id=post_id)

@blueprint.route('/deletePost.html/<category_id>/<post_id>', methods=['GET', 'POST'])
@login_required
def deletePost(category_id=None, post_id=None):
    print('Мы здесь', category_id, post_id)
    if post_id != '-1':
        # Соберем все посты у которых этот родитель
        currPost = Post.query.get(post_id)
        parentPost=Post.query.get(currPost.parentPost)
        if not parentPost:
            category_id=currPost.category_id
            post_id=currPost.id
        else:
            category_id = parentPost.category_id
            post_id = parentPost.id
        childs = Post.query.filter(Post.parentPost==currPost.id).all()
        #И меняем у них родителя
        if len(childs)>0:
            for childItem in childs:
                if parentPost:
                    childItem.parentPost= currPost.parentPost
                else:
                # Удаляем родителя ветки, всех детей долой!
                    db.session.delete(childItem)
            db.session.commit()
        db.session.delete(currPost)
        db.session.commit()
    if parentPost:
        return jsonify({'link': url_for('home_blueprint.forumPage', category_id=category_id, post_id=post_id)}) #, catname=catname
    else:
        return jsonify({'link': url_for('home_blueprint.postsTopics', category_id=category_id)})
    # return redirect(url_for('home_blueprint.postsTopics', category_id=category_id))


@blueprint.route('/quotePost.html/<category_id>/<post_id>', methods=['GET', 'POST'])
@login_required
def quotePost(category_id=None, post_id=None):

    post_form = AddPostForm(request.form)
    if 'addPost' in request.form:
        argslst = dict(request.form)
        argslst = {key: argslst[key]  for key in argslst if key not in ['addPost']}
        argslst['user_added'] = current_user.id
        argslst['category_id'] = category_id
        post = Post(**argslst)
        newParent = Post.query.filter(Post.topic_label==post_form.title.data).all()
        if post_id != '-1':
            parentPost=Post.query.get(post_id)
            post.category_id=parentPost.category_id
            if len(newParent)>0:  #есть уже такой топик
                post.parentPost = post_id
            else:
                post.parentPost = None

        # print(post_form.body.data)
        post.topic_label= post_form.title.data
        # print(post_id)
        db.session.add(post)
        db.session.commit()
        if post_id !='-1':
            return redirect(url_for('home_blueprint.forumPage', category_id=parentPost.category_id, post_id=post_id))
        else:
            return redirect(url_for('home_blueprint.postsMain'))
    elif 'Cancel' in request.form:
        parentPost = Post.query.get(post_id)

        return redirect(url_for('home_blueprint.forumPage', category_id=parentPost.category_id, post_id=post_id))
    elif request.method=='GET':
        # print(app.config['CKEDITOR_EXTRA_PLUGINS'])
        if post_id != '-1':
            post_form.post_id.data=post_id
            parentPost= Post.query.get(post_id)
            userAdded = Users.query.get(parentPost.user_added)
            post_form.title.data = parentPost.topic_label
            post_form.body.data = '<figure class="quote"><blockquote><p>Ответ на: </p>' + str(parentPost.body) + '</blockquote>' +\
                  '<figcaption>' + str(userAdded.username) + '</figcaption></figure><br>'

        return render_template('home/quotePost.html', segment='postsMain', form=post_form, category_id=category_id, post_id=post_id)


@blueprint.route('/updateMeta', methods=['GET'])
def updateMeta():
    articles = Article.query.all()
    for currArticle in articles:
        #заполняем только если не заполнено еще
        if (currArticle.video_link!= '') & (not currArticle.video_views):
            if 'youtube' in currArticle.video_link:
                currArticle.video_thumbnail = 'https://img.youtube.com/vi/' + currArticle.video_link.split('=')[
                    1] + '/0.jpg'
                video_id =currArticle.video_link.split('=')[1]
            else:
                currArticle.video_thumbnail = 'https://img.youtube.com/vi/' + currArticle.video_link.split('/')[
                    3] + '/0.jpg'
                video_id = currArticle.video_link.split('/')[3]
            #Заполним так же мета информацию по видео
            yt = YouTube('https://www.youtube.com/watch?v=' +video_id )
            currArticle.video_author = yt.author
            currArticle.video_description = yt.description
            currArticle.video_name = yt.title
            currArticle.video_uploadDate = yt.publish_date.strftime("%Y-%m-%d")
            currArticle.video_ageRestricted = yt.age_restricted
            currArticle.video_rating = yt.rating
            currArticle.video_views = yt.views
            currArticle.video_keywords = ', '.join(yt.keywords)
            # print(article.video_keywords)
            hours = int(yt.length / 3600)
            minutes = int((yt.length - hours * 3660) / 60)
            seconds = int(yt.length - hours * 3600 - minutes * 60)
            currArticle.video_duration = 'PT' + str(hours) + 'H' + str(minutes) +'M' + str(seconds) + 'S'
            #количество комментариев
            params = {
                'part': 'statistics',
                'id': video_id,
                'key': app.config['YT_APIKEY']
            }
            d = requests.get('https://www.googleapis.com/youtube/v3/videos', params=params).json()
            if 'commentCount' in d['items'][0]['statistics']:
                currArticle.video_commentsCount = d['items'][0]['statistics']['commentCount']
            else:
                currArticle.video_commentsCount = 0
                # print(d['items'][0]['statistics'])
            if 'likeCount' in d['items'][0]['statistics']:
                currArticle.video_likes = d['items'][0]['statistics']['likeCount']
            else:
                currArticle.video_likes=0

            db.session.add(currArticle)
            db.session.commit()
    return render_template('home/index.html', segment='index')

#список всех статей
@blueprint.route('/articlesMain.html', methods=['GET'])
# @login_required
def articlesMain():

    def makeLink(id, name):
        return '<a href = "' + url_for('home_blueprint.editarticle', article_id=str(id)) + \
               '">' + str(name) + '</a>'
    def selectArticlePhoto(thumbnail, photo):
        return photo if photo else thumbnail

    # page = request.args.get('page', 1, type=int)
    dfArticles = pd.read_sql('''SELECT  art.id, art.title, art.user_added, art.video_thumbnail,
            (SELECT atf.photo FROM ArticlePhotos atf WHERE atf.article_id = art.id ORDER BY Photo ASC LIMIT 1) AS Photo
            FROM Articles art  ORDER BY art.update_date DESC;''', db.session.bind)
    #Из Activity рассчитаем среднюю оценку
    query = db.session.query(Activity.query.with_entities(Activity.article_id, func.avg(Activity.rating)).\
            group_by(Activity.article_id).subquery())
    dfRating = pd.read_sql(query.statement, db.session.bind)
    dfRating.rename(columns={'article_id': 'id', 'avg_1': 'rating'}, inplace=True)
    dfRating.dropna(subset=['rating'], inplace=True)
    print(dfRating)
    if not dfRating.empty:
        dfRating['rating'] = dfRating['rating'].round(1)
    dfArticles = dfArticles.merge(dfRating, on='id', how='left')

    #Из Activity рассчитаем количество комментариев
    query = db.session.query(Comment.query.with_entities(Comment.article_id, func.count()).\
            group_by(Comment.article_id).subquery())
    dfComments = pd.read_sql(query.statement, db.session.bind)
    dfComments.rename(columns={'article_id':'id', 'count_1':'comments'}, inplace=True)
    if len(dfComments.loc[~dfComments['id'].isna()]) >0:
        dfArticles = dfArticles.merge(dfComments, on='id', how='left')
    else:
        dfArticles['comments'] = 0
    dfArticles['comments'].fillna(0, inplace=True)
    dfArticles['comments']=dfArticles['comments'].astype(int)


    dfArticles['Photo'] = dfArticles['Photo'].apply( lambda x: url_for('static',
                    filename=os.path.join(app.config['PHOTOS_FOLDER'], x).replace('\\','/')) if x else None)
    dfArticles['Photo'] = dfArticles.apply(lambda x: selectArticlePhoto(x.video_thumbnail, x.Photo), axis=1)

    dfArticles['Photo'] = dfArticles['Photo'].apply( lambda x: '<img  src=' + x + ' width="350px" height="350px" class="img-fluid rounded-0 alt="">' if x else '')
    dfArticles['Photo'] = dfArticles.apply(lambda x: makeLink(x['id'], x['Photo']), axis=1)
    dfArticles['title'] = dfArticles.apply(lambda x: makeLink(x['id'], x['title']), axis=1)
    dfArticles['id'] = dfArticles['id'].apply \
        (lambda x: '<a href = "' + url_for('home_blueprint.editarticle', article_id=str(x)) +
                   '">' + str(x) + '</a>')
    dfArticles = dfArticles[['id', 'Photo', 'title', 'rating', 'comments']]
    # print(dfArticles.head())

    page = request.args.get('page', 1, type=int)
    #выбираем только записи нужной страницы
    pagesCount = ceil(len(dfArticles.index)/app.config['ARTICLES_PER_PAGE'])


    dfArticles = dfArticles[app.config['ARTICLES_PER_PAGE'] * (page-1):app.config['ARTICLES_PER_PAGE'] * (page)]

    return render_template('home/articlesMain.html', segment='articlesMain', row_data=list(dfArticles.values.tolist()),
                           currPage=page, pagesCount=pagesCount) #

@blueprint.route('/files/<filename>')
@csrf.exempt
def uploaded_files(filename):
    path = app.config['UPLOADED_PATH']
    return send_from_directory(path, filename)


@blueprint.route('/upload', methods=['POST'])
@csrf.exempt
def upload():
    f = request.files.get('upload')
    # print('Here')
    extension = f.filename.split('.')[1].lower()
    if extension not in ['jpg', 'gif', 'png', 'jpeg']:
        return upload_fail(message='Image only!')
    unique_filename = str(uuid.uuid4())
    f.filename = unique_filename + '.' + extension
    f.save(os.path.join(app.config['UPLOADED_PATH'], f.filename))
    url = url_for('home_blueprint.uploaded_files', filename=f.filename)
    return upload_success(url=url)


@blueprint.route('/edititem.html/addNewComment', methods=['POST'])
@blueprint.route('/editarticle.html/addNewComment', methods=['POST'])
@login_required
def addNewComment():
    s = request.get_json(force=True)
    if 'item_id' in s:
        currItem = Item.query.get(s['item_id'])
    elif 'article_id' in s:
        currItem = Article.query.get(s['article_id'])
    newComment = currItem.add_emptycomment(current_user)
    db.session.query(Comment).filter(Comment.id == newComment.id).\
        update({Comment.text:s['value']}, synchronize_session="fetch")
    db.session.commit()
    return jsonify({'result': 'success'})

def UpdateActivities():
    '''Добавляет все продукты текущему пользователю, даже если  он их не создавал
     Значение по умолчанию InList = True, haveIt=False'''
    allItems = Item.query.with_entities(Item.id).all()
    itemsList = [r[0] for r in allItems] #перевели список enum'ов в list
    Activities = Activity.query.with_entities(Activity.item_id).filter(Activity.user_id == current_user.id).all()
    activitiesList = [r[0] for r in Activities] #перевели список enum'ов в list
    listToAdd = list(elem for elem in itemsList if elem not in activitiesList)
    print(listToAdd)
    for item in listToAdd:
        newactivity = Activity(item_id=item, User=current_user, inList=False,
                               haveIt=False)
        db.session.add(newactivity)
    db.session.commit()
    return


#Снимаем с или ставим продвижение Авито
@blueprint.route('/changeItemState', methods=['POST'])
@login_required
def changeItemState():
    sites_dict={'idHaveIt':'haveIt',
                'inList':'inList'
    }
    s = request.get_json(force=True)
    btnName = str(sites_dict.get(s['id'].split('_')[0]))
    idItem = str(s['id'].split('_')[1])
    updateDict= {btnName: s['value']}  #значение value берем из параметров post
    #Меняем статус публикации объявления в базе данных
    db.session.query(Activity).filter((Activity.item_id == idItem) & (Activity.user_id == current_user.id)). \
            update(updateDict, synchronize_session="evaluate")
    db.session.commit()
    return jsonify({'id': idItem, 'button':btnName, 'status':s['value']})


#меняем состояние фильтра для пользователя
@blueprint.route('/changeFilterNow', methods=['POST'])
@login_required
def changeFilterNow():

    s = request.get_json(force=True)
    # print(s)
    categoryID = s['id'].split('_')[1]

    #Если для текущего пользователя нет фильтров в таблице -  Добавляем все фильтры
    categories = Category.query.all()
    for cat in categories:
        existingFilter = UserCatFilters.query.filter(UserCatFilters.user == current_user.id,
                                                     UserCatFilters.category == cat.id).first()
        if not existingFilter:
            userFilter = UserCatFilters(current_user, cat)
            db.session.add(userFilter)
            db.session.commit()
    catFilter = UserCatFilters.query.filter(UserCatFilters.user==current_user.id, UserCatFilters.category==categoryID).first()
    catFilter.value = s['value']
    db.session.commit()

    return jsonify({'result': 'success'})

@blueprint.route('/save_personnal_photo', methods=['POST'])
@login_required
def save_personnal_photo():
    # print(request.files.get('persoPhoto'))
    myFile=request.files.get('persoPhoto')
    # print(myFile)
    photo1 = secure_filename(myFile.filename)
    if photo1:
        new_filename = current_user.username + "_" + photo1
        myFile.save(os.path.join(app.config['PERSO_PHOTO_FOLDER'], new_filename))
        current_user.avatar_photo=os.path.join(app.config['PERSO_PHOTO'], new_filename).replace('\\', '/')
        db.session.commit()
    return jsonify({'result':  url_for('static', filename=current_user.avatar_photo)})

@blueprint.route('/downloadItemsFile3', methods=['GET'])
def downloadItemsFile3():
    # return send_from_directory('static', 'assets/uploads/denis_2022_10_29_20_50_56.xlsx', as_attachment=True)
    if current_user.is_anonymous:
        query = db.session.query(Item, Category).with_entities(Item.id, Category.catname, Item.name, Item.description,
                Item.price)\
                .join(Activity, Category).group_by(Item.id)
        dfItemsList = pd.read_sql(query.statement, query.session.bind)
        dfItemsList = dfItemsList[['id', 'catname', 'name', 'description', 'price']]
        user = 'Anonim'
    else:
        query = db.session.query(Item, Activity, Category).join(Activity, Category)\
            .filter((Activity.inList == True) & (Activity.user_id == current_user.id))
        dfItemsList = pd.read_sql(query.statement, query.session.bind)
        dfItemsList = dfItemsList[['id', 'catname', 'name', 'description', 'price', 'rating', 'haveIt']]
        dfItemsList.rename(columns={'rating': 'Ваша оценка', 'haveIt': 'Уже в наличии'}, inplace=True)
        user = current_user.username

    #считаем средний рейтинг
    query = db.session.query(Activity.query.with_entities(Activity.item_id, func.avg(Activity.rating), func.count()).\
            group_by(Activity.item_id).subquery())
    dfRating = pd.read_sql(query.statement, db.session.bind)
    dfRating.rename(columns={'item_id':'id', 'avg_1':'rating', 'count_1':'Кол-во оценок'}, inplace=True)
    dfRating['rating'] = dfRating['rating'].round(1)
    dfItemsList = dfItemsList.merge(dfRating, on='id', how='left')
    dfItemsList.rename(columns={'rating':'Средняя оценка', 'catname':'Категория', 'name':'Наименование',
                                'description':'Описание', 'price':'Цена'}, inplace=True)

    dfItemsList.drop(columns=['id'], inplace=True)
    fileName = user + '.xlsx'
    filePath = os.path.join(app.config['ITEMFILES_PATH'], fileName)
    with pd.ExcelWriter(filePath, engine='xlsxwriter') as wb:
        dfItemsList.to_excel(wb, sheet_name='Sheet1', index=False)
        sheet = wb.sheets['Sheet1']
        sheet.autofilter('A1:H' + str(dfItemsList.shape[0]))
        # print(dfItemsList.shape[0])
        cell_format = wb.book.add_format()
        cell_format.set_font_color('white')
        cell_format.set_bg_color('#4F81BD')
        cell_format.set_bold()
        sheet.set_column('A:B', 18)
        sheet.set_column('C:C', 30)
        sheet.set_column('D:H', 15)
        sheet.write_row(0, 0, dfItemsList.columns, cell_format)
        # dfItemsList.to_excel(filePath, index=False)
    time.sleep(1)
    # filePath = os.path.join(app.config['ITEMFILES_PATH'] + '/' + fileName).replace('\\', '/')
    # print(filePath)

    return make_response(jsonify({'buttonId': user}), 200)



@blueprint.route('/<template>')
@login_required
def route_template(template):
    # print('Мы на template')
    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None

