import os
import time
import logging

import psutil

from . import imptool
from .lib.config import load_config
from .lib.logging import logger
from .env import Env


def pkginfo():
    components = (
        'core',
        'sentry',
        'pyramid',
        'gui',
        'jsrealm',
        'auth',
        'resource',
        'resmeta',
        'social',
        'spatial_ref_sys',
        'layer',
        'layer_preview',
        'feature_layer',
        'feature_description',
        'feature_attachment',
        'render',
        'svg_marker_library',
        'webmap',
        'file_storage',
        'vector_layer',
        'lookup_table',
        'postgis',
        'raster_layer',
        'raster_mosaic',
        'raster_style',
        'wfsserver',
        'wfsclient',
        'wmsclient',
        'wmsserver',
        'tmsclient',
        'file_upload',
        'audit',
    )

    return dict(
        components={
            comp: dict(
                module='nextgisweb.{}'.format(comp),
                enabled=comp not in ('wfsclient', 'raster_mosaic')
            ) for comp in components
        },
        amd_packages=[(k, 'external/{}'.format(k)) for k in (
            'dojo', 'dijit', 'dojox', 'dgrid', 'xstyle', 'put-selector',
            'handlebars', 'jed', 'codemirror', 'proj4', 'jquery',
        )],
    )


def main(global_config=None, **settings):
    """ This function returns a Pyramid WSGI application. """

    env = Env(cfg=load_config(None, None), initialize=True, set_global=True)
    config = env.pyramid.make_app({})
    app = config.make_wsgi_app()
    _log_startup_time()
    return app


def _log_startup_time(level=logging.INFO):
    if logger.isEnabledFor(level):
        psinfo = psutil.Process(os.getpid())
        startup_time = int(1000 * (time.time() - psinfo.create_time()))
        logger.log(level, "WSGI startup took %d msec", startup_time)


# TODO: Remove in 4.5.0.dev0, entrypoint already removed
def amd_packages():
    return ()
