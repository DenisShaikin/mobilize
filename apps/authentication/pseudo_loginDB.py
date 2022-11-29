from apps.authentication.pseudo_login import PseudoUser
from apps import db
from apps.authentication.models import Users, Category, UserCatFilters, Item, Activity
import uuid


class PseudoUserDB(PseudoUser):

    def __init__(self):
            self.init_app(app, add_context_processor)


    def init_app(self, app, add_context_processor=True, ddays=30):
        '''
        Configures an application. This registers an `after_request` call, and
        attaches this `pseudoUser` to it as `app.pseudoUser`.

        :param app: The :class:`flask.Flask` object to configure.
        :type app: :class:`flask.Flask`
        :param add_context_processor: Whether to add a context processor to
            the app that adds a `current_user` variable to the template.
            Defaults to ``True``.
        :type add_context_processor: bool
        '''
        app.pseudoUser = self
        self.initSessionUser(ddays)
        # app.after_request(self._update_remember_cookie)

        # if add_context_processor:
        #     app.context_processor(_user_context_processor)

    def initSessionUser(self, ddays=30):
        '''
        Удаляет всех псевдо пользователей с возрастом старше ddays дней
        :return:
        '''
        #Удалим всех пользователей без пароля старше месяца
        oldUsers=Users.query.filter((Users.password==None) & (Users.timestamp < datetime.utcnow()-timedelta(days=ddays))).all()
        for old in oldUsers:
            db.session.delete(old)
            db.session.commit()

    def getSessionUser(self):
        bNewUser=False
        #А теперь создадим нового или выберем существующего
        if 'pseudoUser' in session:
            tempUserName = session['pseudoUser']
            user = Users.query.filter(Users.username==tempUserName).first()
            if not user:
                bNewUser=True
                user = Users(username=tempUserName)
                db.session.add(user)
                db.session.commit()
        else:
            bNewUser=True
            tempUserName= str(uuid.uuid4())
            session['pseudoUser'] = tempUserName
            user = Users(username=tempUserName)
            db.session.add(user)
            db.session.commit()
        #Если пользователь новый -создаем все фильтры категорий для него
        if bNewUser:
            categories = Category.query.all()
            for cat in categories:
                userFilter = UserCatFilters(user, cat)
                db.session.add(userFilter)
                db.session.commit()
            self.UpdateActivities(user)
        return user

    def UpdateActivities(user):
        '''Добавляет все продукты текущему пользователю, даже если  он их не создавал
         Значение по умолчанию InList = True, haveIt=False'''
        # Проверим что еще нет вещей у user
        itemsNow = Item.query.with_entities(Item.id, Activity.id).join(Activity).filter(
            Activity.user_id == user.id).all()
        print(itemsNow)
        if len(itemsNow) == 0:
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