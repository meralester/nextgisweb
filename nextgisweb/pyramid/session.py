# -*- coding: utf-8 -*-
from __future__ import division, absolute_import, print_function, unicode_literals

from datetime import datetime, timedelta

import transaction
from pyramid.interfaces import ISession
from sqlalchemy.orm.exc import NoResultFound
from zope.interface import implementer

from ..models import DBSession

from .model import Session, SessionStore
from .util import gensecret, datetime_to_unix

__all__ = ['WebSession']

cookie_settings = dict(
    path='/',
    domain=None,
    httponly=True,
    samesite='Lax'
)


@implementer(ISession)
class WebSession(dict):
    def __init__(self, request):
        self._validated = False
        self._updated = list()
        self._cleared = False
        self._deleted = list()
        self._cookie_name = request.env.pyramid.options['session.cookie.name']
        self._cookie_max_age = request.env.pyramid.options['session.max_age']
        self._session_id = request.cookies.get(self._cookie_name)

        if self._session_id is not None:
            try:
                actual_date = datetime.utcnow() - timedelta(seconds=self._cookie_max_age)
                session = Session.filter(
                    Session.id == self._session_id,
                    Session.last_activity > actual_date).one()
                self.new = False
                self.created = datetime_to_unix(session.created)
            except NoResultFound:
                self._session_id = None

        if self._session_id is None:
            self.new = True
            self.created = datetime_to_unix(datetime.utcnow())

        def check_save(request, response):
            nothing_to_update = len(self._updated) == 0
            nothing_to_delete = (not self._cleared and len(self._deleted) == 0) \
                or self._session_id is None
            if nothing_to_update and nothing_to_delete:
                return

            with transaction.manager:
                if self._session_id is not None:
                    if self._cleared:
                        SessionStore.filter(
                            SessionStore.session_id == self._session_id,
                            ~SessionStore.key.in_(self._updated)
                        ).delete(synchronize_session=False)
                    elif len(self._deleted) > 0:
                        SessionStore.filter(
                            SessionStore.session_id == self._session_id,
                            SessionStore.key.in_(self._deleted)
                        ).delete(synchronize_session=False)
                    try:
                        session = Session.filter_by(id=self._session_id).one()
                    except NoResultFound:
                        self._session_id = None

                if self._session_id is None:
                    session = Session(
                        id=gensecret(32),
                        created=datetime.utcnow()
                    )

                session.last_activity = datetime.utcnow()

                with DBSession.no_autoflush:
                    for key in self._updated:
                        try:
                            kv = SessionStore.filter_by(session_id=session.id, key=key).one()
                        except NoResultFound:
                            kv = SessionStore(session_id=session.id, key=key).persist()
                        kv.value = self._get(key)

                session.persist()

            cookie_settings['secure'] = request.scheme == 'https'
            cookie_settings['max_age'] = self._cookie_max_age
            response.set_cookie(self._cookie_name, value=session.id, **cookie_settings)

        request.add_response_callback(check_save)

    def _get(self, key):
        return super(WebSession, self).__getitem__(key)

    def _set(self, key, value):
        super(WebSession, self).__setitem__(key, value)

    @property
    def _keys(self):
        return super(WebSession, self).keys()

    def _validate_all(self):
        if self._validated:
            return
        for kv in SessionStore.filter(SessionStore.session_id == self._session_id,
                                      ~SessionStore.key.in_(self._keys)).all():
            self._set(kv.key, kv.value)
        self._validated = True

    def _validate(self, key):
        if self._validated or key in self._keys:
            return
        if key not in self._deleted:
            try:
                kv = SessionStore.filter_by(session_id=self._session_id, key=key).one()
                self._set(key, kv.value)
            except NoResultFound:
                pass

    # ISession

    def flash(self, msg, queue='', allow_duplicate=True):
        raise NotImplementedError()

    def pop_flash(self, queue=''):
        raise NotImplementedError()

    def peek_flash(self, queue=''):
        raise NotImplementedError()

    # dict

    def __contains__(self, key, *args, **kwargs):
        self._validate(key)
        return super(WebSession, self).__contains__(key, *args, **kwargs)

    def keys(self, *args, **kwargs):
        self._validate_all()
        return super(WebSession, self).keys(*args, **kwargs)

    def values(self, *args, **kwargs):
        self._validate_all()
        return super(WebSession, self).values(*args, **kwargs)

    def items(self, *args, **kwargs):
        self._validate_all()
        return super(WebSession, self).items(*args, **kwargs)

    def __len__(self, *args, **kwargs):
        self._validate_all()
        return super(WebSession, self).__len__(*args, **kwargs)

    def __getitem__(self, key, *args, **kwargs):
        self._validate(key)
        return super(WebSession, self).__getitem__(key, *args, **kwargs)

    def get(self, key, *args, **kwargs):
        self._validate(key)
        return super(WebSession, self).get(key, *args, **kwargs)

    def __iter__(self, *args, **kwargs):
        self._validate_all()
        return super(WebSession, self).__iter__(*args, **kwargs)

    def __setitem__(self, key, *args, **kwargs):
        if key not in self._updated:
            self._updated.append(key)
        if key in self._deleted:
            self._deleted.remove(key)
        return super(WebSession, self).__setitem__(key, *args, **kwargs)

    def setdefault(self, *args, **kwargs):
        raise NotImplementedError()

    def update(self, *args, **kwargs):
        raise NotImplementedError()

    def __delitem__(self, key, *args, **kwargs):
        if key not in self._deleted:
            self._deleted.append(key)
        if key in self._updated:
            self._updated.remove(key)
        return super(WebSession, self).__delitem__(key, *args, **kwargs)

    def pop(self, *args, **kwargs):
        raise NotImplementedError()

    def popitem(self, *args, **kwargs):
        raise NotImplementedError()

    def clear(self, *args, **kwargs):
        self._updated.clear()
        self._deleted.clear()
        self._cleared = True
        return super(WebSession, self).clear(*args, **kwargs)
