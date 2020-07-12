# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from contextlib import contextmanager

import pytest


def _env_initialize():
    import nextgisweb.env
    result = nextgisweb.env.env()
    if result:
        return result
    result = nextgisweb.env.Env()
    result.initialize()
    nextgisweb.env.setenv(result)
    return result


@pytest.fixture(scope='session')
def env():
    return _env_initialize()


@pytest.fixture
def txn():
    from nextgisweb.models import DBSession
    from transaction import manager
    _env_initialize()
    with manager as t:
        yield t
        try:
            DBSession.flush()
            t.abort()
        finally:
            DBSession.expunge_all()
            DBSession.expire_all()


@pytest.fixture(scope='session')
def webapp(env):
    from webtest import TestApp
    app = env.pyramid.make_app({}).make_wsgi_app()
    tapp = TestApp(app)
    yield tapp


@pytest.fixture()
def webapp_handler(env, webapp):
    pyramid = env.pyramid

    @contextmanager
    def _decorator(handler):
        assert pyramid.test_request_handler is None
        try:
            pyramid.test_request_handler = handler
            yield
        finally:
            pyramid.test_request_handler = None

    yield _decorator
    pyramid.test_request_handler = None
