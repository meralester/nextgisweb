# -*- coding: utf-8 -*-
import codecs
from ConfigParser import ConfigParser

from pyramid.config import Configurator
from pyramid.paster import setup_logging
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from sqlalchemy import engine_from_config

from .models import (
    DBSession,
    Base,
)

from .component import Component, load_all
from .env import Env, setenv


def pkginfo():
    components = (
        'core',
        'pyramidcomp',
        'auth',
        'security',
        'resource',
        'spatial_ref_sys',
        'layer',
        'feature_layer',
        'feature_description',
        'feature_photo',
        'style',
        'marker_library',
        'webmap',
        'file_storage',
        'vector_layer',
        'postgis',
        'raster_layer',
        'raster_style',
        'wmsclient',
        'file_upload',
    )

    return dict(
        components=dict(map(
            lambda (i): (i, "nextgisweb.%s" % i),
            components)
        )
    )


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application. """

    if 'logging' in settings:
        setup_logging(settings['logging'])

    cfg = ConfigParser()
    cfg.readfp(codecs.open(settings['config'], 'r', 'utf-8'))

    env = Env(cfg)
    env.initialize()

    setenv(env)

    config = env.pyramid.make_app(settings)
    return config.make_wsgi_app()


def amd_packages():
    return (
        # Сторонние пакеты
        ('dojo', 'nextgisweb:amd_packages/contrib/dojo'),
        ('dijit', 'nextgisweb:amd_packages/contrib/dijit'),
        ('dojox', 'nextgisweb:amd_packages/contrib/dojox'),
        ('cbtree', 'nextgisweb:amd_packages/contrib/cbtree'),
        ('xstyle', 'nextgisweb:amd_packages/contrib/xstyle'),
        ('put-selector', 'nextgisweb:amd_packages/contrib/put-selector'),
        ('dgrid', 'nextgisweb:amd_packages/contrib/dgrid'),

        # Пакеты nextgisweb
        ('ngw', 'nextgisweb:amd_packages/ngw'),
        ('security', 'nextgisweb:amd_packages/security'),
        ('layer_group', 'nextgisweb:amd_packages/layer_group'),
        ('layer', 'nextgisweb:amd_packages/layer'),
        ('style', 'nextgisweb:amd_packages/style'),
        ('feature_layer', 'nextgisweb:amd_packages/feature_layer'),
        ('feature_description', 'nextgisweb:amd_packages/feature_description'),
        ('feature_photo', 'nextgisweb:amd_packages/feature_photo'),
        ('webmap', 'nextgisweb:amd_packages/webmap'),
        ('vector_layer', 'nextgisweb:amd_packages/vector_layer'),
        ('raster_layer', 'nextgisweb:amd_packages/raster_layer'),
        ('raster_style', 'nextgisweb:amd_packages/raster_style'),
        ('wmsclient', 'nextgisweb:amd_packages/wmsclient'),

        # Пакеты компонентов
        ('ngw-resource', 'nextgisweb:resource/amd/ngw-resource'),
        ('ngw-postgis', 'nextgisweb:postgis/amd/ngw-postgis'),
    )
