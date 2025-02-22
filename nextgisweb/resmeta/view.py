from ..resource import Widget, Resource
from .util import _


class Widget(Widget):
    resource = Resource
    operation = ('create', 'update')
    amdmod = 'ngw-resmeta/Widget'


def setup_pyramid(comp, config):
    Resource.__psection__.register(
        key='resmeta', title=_("Metadata"), priority=40,
        is_applicable=lambda obj: len(obj.resmeta) > 0,
        template='section.mako')
