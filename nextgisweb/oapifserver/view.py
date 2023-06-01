from ..resource import Widget, Resource
from .model import Service

from .util import _


class ServiceWidget(Widget):
    resource = Service
    operation = ('create', 'update')
    amdmod = 'ngw-oapifserver/ServiceWidget'


def setup_pyramid(comp, config):
    Resource.__psection__.register(
        key="description", title=_("External access"),
        is_applicable=lambda obj: obj.cls == 'oapifserver_service',
        template='section_api_oapif.mako')