# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, request, redirect, url_for, jsonify
from flask import send_from_directory, make_response
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from apps.home.forms import AddItemForm, EditItemForm, SettingsForm
from sqlalchemy import func
from apps.authentication.models import Users
from apps import db
from apps.authentication.models import Category, ItemPhotos, Item, Activity, Comment
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import pandas as pd
from flask import current_app as app
import time


@blueprint.route('/index')
def index():
    return render_template('home/index.html', segment='index')

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
@login_required
def main():
    def makeSelectedButton(selectedState, haveItState, id, user):
        if selectedState:
            result = '''<div class="form-switch" > <input class="form-check-input" type="checkbox" name="inList_''' + str(id) \
               + '''" id="inList_''' + str(id) + '" checked ' + ''' onclick=changeSelected("inList_''' + str(id) + '''")> 
               <label class ="form-check-label" for ="inList_''' + str(id) + '''"> В списке </label></div>'''
        else:
            result =  '''<div class="form-switch" > <input class="form-check-input" type="checkbox" name="inList_''' + str(id) \
                   + '''" id="inList_''' + str(id) + '" ' + ''' onclick=changeSelected("inList_''' + str(id) + '''")>
                   <label class ="form-check-label" for ="inList_''' + str(id) + '''"> В списке </label></div>'''
        if haveItState:
            result = result + ''' <div class="form-switch" > <input class="form-check-input" type="checkbox" name="idHaveIt_''' + str(id) \
                     + '''" id="idHaveIt_''' + str(id) + '" checked ' + ''' onclick=changeSelected("idHaveIt_''' + str(id) + '''")>
                     <label class ="form-check-label" for ="idHaveIt_''' + str(id) + '''"> Уже есть </label></div>'''
        else:
            result = result + '''<div class="form-switch" > <input class="form-check-input" type="checkbox" name="idHaveIt_''' + str(id) \
                     + '''" id="idHaveIt_''' + str(id) + '" ' + ''' onclick=changeSelected("idHaveIt_''' + str(id) + '''")>
                     <label class ="form-check-label" for ="idHaveIt_''' + str(id) + '''"> Уже есть </label></div>'''
        return result

    def makeLink(id, name):
        return '<a href = "' + url_for('home_blueprint.edititem', item_id=str(id)) + \
               '">' + str(name) + '</a>'

    page = request.args.get('page', 1, type=int)

    dfItems = pd.read_sql('''SELECT  itm.id, itm.name, itm.price, itm.user_added, ctg.catname, act.inList, act.haveIt,
            (SELECT itf.photo FROM ItemPhotos itf WHERE itf.item_id = itm.id ORDER BY Photo ASC LIMIT 1) AS Photo
            FROM Items itm LEFT JOIN Categories ctg ON (ctg.id = itm.category)
            LEFT JOIN Activity act ON (act.item_id = itm.id) WHERE act.user_id=''' + str(current_user.id) +';', db.session.bind)
    #Из Activity рассчитаем среднюю оценку
    query = db.session.query(Activity.query.with_entities(Activity.item_id, func.avg(Activity.rating)).\
            group_by(Activity.item_id).subquery())
    dfRating = pd.read_sql(query.statement, db.session.bind)
    dfRating.rename(columns={'item_id':'id', 'avg_1':'rating'}, inplace=True)
    dfRating['rating'] = dfRating['rating'].round(1)
    dfItems = dfItems.merge(dfRating, on='id', how='left')

    #выбираем только записи нужной страницы
    pagesCount = round(len(dfItems.index)/app.config['ITEMS_PER_PAGE'])
    dfItems = dfItems[app.config['ITEMS_PER_PAGE'] * (page-1):app.config['ITEMS_PER_PAGE'] * (page)]

    # print(dfRating)
    # print(dfItems.head())
    dfItems['selected'] = dfItems['inList']
    dfItems['selected'] = dfItems.apply(lambda x: makeSelectedButton(x.selected, x.haveIt, x.id, x.user_added), axis=1)
    dfItems = dfItems[['Photo', 'id', 'selected', 'catname', 'name', 'rating', 'price']]
    dfItems['Photo'] = dfItems['Photo'].apply( lambda x: url_for('static',
                    filename=os.path.join(app.config['PHOTOS_FOLDER'], x).replace('\\','/')) if x else None)

    dfItems['name'] = dfItems.apply(lambda x: makeLink(x['id'], x['name']), axis=1)
    dfItems['id'] = dfItems['id'].apply \
        (lambda x: '<a href = "' + url_for('home_blueprint.edititem', item_id=str(x)) +
                   '">' + str(x) + '</a>')
    return render_template('home/main.html', segment='main', row_data=list(dfItems.values.tolist()),
                           currPage=page, pagesCount=pagesCount) #

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
        db.session.add(item)
        for file in request.files.getlist('photos'):  #additem_form.photos.data
            photo = secure_filename(file.filename)
            if photo:
                new_filename = current_user.username + "_" + datetime.today().strftime('%Y_%m_%d_%H_%M_%S') + "_" + photo
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                newphoto = ItemPhotos(Item=item, photo=new_filename)
                db.session.add(newphoto)
        newactivity = Activity(Item=item, User=current_user, inList=True if argslst['inList']=='y' else False,
                               haveIt=True if argslst['inList']=='y' else False, rating=argslst['rating'])
        db.session.add(newactivity)
        db.session.commit()
        return redirect(url_for('home_blueprint.main'))
    return render_template('home/additem.html', segment='additem', form = additem_form)

@blueprint.route('/edititem.html/<item_id>', methods=['GET', 'POST'])
@login_required
def edititem(item_id):
    def createPhotoLink(id, photo):
        return '''<figure class="figure"> 
                <img id=photo_''' + str(id) + ' src="'+ url_for('static',
                filename=os.path.join(app.config['PHOTOS_FOLDER'], photo).replace('\\','/'))\
               + '''"  width="150px" height="150px" class="img-fluid rounded-0 alt="">
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
        for file in request.files.getlist('photos'):  #additem_form.photos.data
            photo = secure_filename(file.filename)
            if photo:
                new_filename = current_user.username + "_" + datetime.today().strftime('%Y_%m_%d_%H_%M_%S') + "_" + photo
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                newphoto = ItemPhotos(Item=item, photo=new_filename)
                db.session.add(newphoto)
        editActivity = Activity.query.filter(Activity.item_id == item_id, Activity.user_id==current_user.id).first()
        setattr(editActivity, 'rating', argslst['rating'])
        setattr(editActivity, 'inList', True if 'inList' in argslst else False)
        setattr(editActivity, 'haveIt', True if 'haveIt' in argslst else False)

        db.session.commit()
        return redirect(url_for('home_blueprint.main'))
    elif 'Cancel' in request.form:
        return redirect(url_for('home_blueprint.main'))

    elif request.method == 'GET':
        # Все поля может редактировать только создатель Item

        values = db.session.query(Item, Category, Activity).with_entities(
            Item.id, Item.user_added, Item.name,  Item.description, Item.price,
            Item.category, Category.catname, Activity.inList, Activity.haveIt,
            Activity.rating).join(Category, Activity).filter(Item.id == item_id, Activity.user_id==current_user.id).first()

        if not values: #На этого пользователя нет записи с рейтингом - другой делал товар
            currItem = Item.query.filter(Item.id == item_id).first()
            newactivity = Activity(Item=currItem, User=current_user, inList=False,
                                   haveIt=False)
            db.session.add(newactivity)
            db.session.commit()
            values = db.session.query(Item, Category, Activity).with_entities(
                Item.id, Item.name, Item.description, Item.price,
                Item.category, Category.catname, Activity.inList, Activity.haveIt,
                Activity.rating).join(Category, Activity).filter(Item.id == item_id,
                                                                 Activity.user_id == current_user.id).first()

        values = values._mapping
        owner = True if values.user_added == current_user.id else False  #Редактирует создатель Item
        # print(values)
        edititem_form.category.default = values['category']
        edititem_form.process()
        edititem_form.name.data = values['name']

        edititem_form.description.data = values['description']
        edititem_form.price.data = values['price']
        # print(edititem_form.price.data)
        edititem_form.inList.data = values['inList']
        edititem_form.haveIt.data = values['haveIt']
        edititem_form.rating.data = values['rating']

        # photos = db.session.query(ItemPhotos).filter(ItemPhotos.item_id == item_id).all()
        query = db.session.query(ItemPhotos).filter(ItemPhotos.item_id == item_id)
        dfPhotos = pd.read_sql(query.statement, query.session.bind)
        if not dfPhotos.empty:
            # print(dfPhotos)
            dfPhotos['photo'] = dfPhotos.apply(lambda x: createPhotoLink(x.id, x.photo), axis=1)

        currItem = Item.query.filter(Item.id == item_id).first()
        newComment = currItem.add_emptycomment(current_user)
        comments = currItem.followed_comments(current_user).all()
        # print(comments)
        dfComments = pd.DataFrame.from_records(comments, index='id', columns=['id', 'user', 'text'])
        # print(dfComments)
        return render_template('home/edititem.html', segment='edititem', form=edititem_form,
                               photos=list(dfPhotos['photo'].values.tolist()),
                               comments_data=list(dfComments.values.tolist()), owner=owner, comment_id=newComment.id)

@blueprint.route('/edititem.html/addNewComment', methods=['POST'])
@login_required
def addNewComment():
    s = request.get_json(force=True)
    db.session.query(Comment).filter(Comment.id == s['item_id']).\
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
    # print(listToAdd)
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

@blueprint.route('/downloadItemsFile', methods=['GET'])
def downloadItemsFile():
    query = db.session.query(Item, Activity, Category).join(Activity, Category).filter((Activity.user_id == current_user.id) & (Activity.inList==True))
    dfItemsList = pd.read_sql(query.statement, query.session.bind)
    dfItemsList = dfItemsList [['id', 'catname', 'name', 'description', 'price', 'rating', 'haveIt']]
    dfItemsList.rename(columns={'rating':'Ваша оценка', 'haveIt':'Уже в наличии'}, inplace=True)
    #считаем средний рейтинг
    query = db.session.query(Activity.query.with_entities(Activity.item_id, func.avg(Activity.rating)).\
            group_by(Activity.item_id).subquery())
    dfRating = pd.read_sql(query.statement, db.session.bind)
    dfRating.rename(columns={'item_id':'id', 'avg_1':'rating'}, inplace=True)
    dfRating['rating'] = dfRating['rating'].round(1)
    # print(dfRating.columns, dfItemsList.columns)
    dfItemsList = dfItemsList.merge(dfRating, on='id', how='left')
    dfItemsList.rename(columns={'rating':'Средняя оценка'}, inplace=True)
    fileName = current_user.username + '_' + datetime.today().strftime('%Y_%m_%d_%H_%M_%S') + '.xlsx'
    filePath = os.path.join(app.config['ITEMFILES_PATH'], fileName)
    dfItemsList.to_excel(filePath)
    time.sleep(1)
    filePath = os.path.join(app.config['ITEMFILES_PATH']).replace('\\', '/')
    # print(filePath)
    # print(currResult)
    # return jsonify({'result': 'success'})
    return make_response(send_from_directory(filePath, fileName, as_attachment=True))
    #redirect(url_for('static', filename=filePath))


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

