from flask import session
from apps import db
from apps.authentication.models import Users, Category, UserCatFilters, Item, Activity
import uuid
from flask_login import current_user, login_user

class PseudoUser(object):
    username=''
    id=''

    def __repr__(self):
        return ''.join(['PseudoUser=', self.username])

    def __init__(self, log_in=True):
        user= self.getSessionUser(log_in)
        return

    def getSessionUser(self, log_in):
        if current_user.is_authenticated:
            if (current_user.password != None):   #нормальный логин, не фейковый
                self.username=current_user.username
                self.id=current_user.id
                return current_user
        bNewUser=False
        #А теперь создадим нового или выберем существующего
        if 'pseudoUser' in session:
            self.username = session['pseudoUser']
            user = Users.query.filter(Users.username==self.username).first()
            if not user:
                bNewUser=True
                user = Users(username=self.username)
                db.session.add(user)
                db.session.commit()

            self.id = user.id
        else:  #нет пользователя в куки, создаем
            bNewUser=True
            self.username= str(uuid.uuid4())
            session['pseudoUser'] = self.username
            session.modified=True
            user = Users(username=self.username)
            db.session.add(user)
            db.session.commit()
            self.id=user.id
        #Если пользователь новый -создаем все фильтры категорий для него
        if bNewUser:
            catFilters = UserCatFilters.query.filter(UserCatFilters.user==user.id).first()
            print(catFilters)
            if not catFilters:
                categories = Category.query.all()
                for cat in categories:
                    userFilter = UserCatFilters(user, cat)
                    db.session.add(userFilter)
                    db.session.commit()
            self.UpdateActivities(user)
        user = Users.query.get(self.id)
        if (user) and (not current_user.is_authenticated) and (log_in):
            login_user(user, remember=True)
        return user

    def UpdateActivities(self, user):
        '''Добавляет все продукты текущему пользователю, даже если  он их не создавал
         Значение по умолчанию InList = True, haveIt=False'''
        # Проверим что еще нет вещей у user
        itemsNow = Item.query.with_entities(Item.id, Activity.id).join(Activity).filter(
            Activity.user_id == user.id).all()
        # print(itemsNow)
        if not itemsNow:
            allItems = Item.query.with_entities(Item.id).all()
            itemsList = [r[0] for r in allItems]  # перевели список enum'ов в list
            Activities = Activity.query.with_entities(Activity.item_id).filter(Activity.user_id == user.id).all()
            activitiesList = [r[0] for r in Activities]  # перевели список enum'ов в list
            listToAdd = list(elem for elem in itemsList if elem not in activitiesList)
            # print(listToAdd)
            for item in listToAdd:
                newactivity = Activity(item_id=item, User=user, inList=False,
                                       haveIt=False)
                db.session.add(newactivity)
            db.session.commit()
        return