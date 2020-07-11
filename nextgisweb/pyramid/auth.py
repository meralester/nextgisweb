# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

from pyramid.authentication import (
    SessionAuthenticationPolicy,
    BasicAuthAuthenticationPolicy as
    PyramidBasicAuthAuthenticationPolicy,
    CallbackAuthenticationPolicy)

from ..auth import User


class BasicAuthenticationPolicy(PyramidBasicAuthAuthenticationPolicy):

    def unauthenticated_userid(self, request):
        """ Standard Pyramid function always returns login as
        userid, but we need number representation of ID. We'll
        swap these by parsing request headers. """

        username = super(BasicAuthenticationPolicy, self) \
            .unauthenticated_userid(request)

        if username is not None:
            user = User.filter_by(keyname=username).first()
            if user is None:
                return None
            else:
                return user.id


class TokenAuthenticationPolicy(CallbackAuthenticationPolicy):

    def unauthenticated_userid(self, request):
        authorization = request.headers.get('Authorization')
        if not authorization:
            return None

        try:
            authmeth, token = authorization.split(' ', 1)
        except ValueError:  # not enough values to unpack
            return None

        if authmeth.lower() != 'bearer':
            return None

        oauth = request.env.auth.oauth
        if oauth is not None:
            user = oauth.access_token_to_user(token)
            if user is not None:
                return user.id

        return None

    def remember(self, request, userid):
        return []

    def forget(self, request):
        return []


class AuthenticationPolicy(object):

    def __init__(self, settings):
        def check(username, password, request):
            user = User.filter_by(keyname=username, disabled=False).first()
            if user is None or not (user.password == password):
                return None
            else:
                return user

        session_auth_policy = SessionAuthenticationPolicy()
        session_auth_policy.userid_key = 'auth.current_user'

        basic_auth_policy = BasicAuthenticationPolicy(
            check=check, realm=b'NextGIS Web')

        token_auth_policy = TokenAuthenticationPolicy()

        self.members = (
            session_auth_policy,
            basic_auth_policy,
            token_auth_policy,
        )

    def authenticated_userid(self, request):
        for m in self.members:
            userid = m.authenticated_userid(request)
            if userid is not None:
                return userid

    def effective_principals(self, request):
        return []

    def remember(self, request, userid):
        headers = []
        for m in self.members:
            res = m.remember(request, userid)
            if res:
                headers.extend(res)

        return headers

    def forget(self, request):
        headers = []
        for m in self.members:
            res = m.forget(request)
            if res:
                headers.extend(res)

        return headers

    def unauthenticated_userid(self, request):
        return None
