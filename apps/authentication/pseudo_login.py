#модуль обслуживает только часть работы с session
#работу с bd обслуживает модуль pseudo_loginBD

from flask import session
import uuid

class PseudoUser(object):
    userName=''
    def __init__(self, app=None, add_context_processor=True):
        if app is not None:
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
        app.pseudo_user = self

        # app.after_request(self._update_remember_cookie)
        # if add_context_processor:
        #     app.context_processor(_user_context_processor)


    def getSessionUser(self):
        #А теперь создадим нового или выберем существующего
        if 'pseudoUser' in session:
            self.userName = session['pseudoUser']
        else:
            self.userName= str(uuid.uuid4())
            session['pseudoUser'] = self.userName
            session.modified = True
        return self.userName

