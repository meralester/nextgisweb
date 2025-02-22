from ..resource import Resource, Widget

from .model import LookupTable
from .util import _


class Widget(Widget):
    resource = LookupTable
    operation = ('create', 'update')
    amdmod = 'ngw-lookup-table/Widget'


def setup_pyramid(comp, config):
    Resource.__psection__.register(
        key='lookup_table', title=_("Lookup table"), priority=10,
        is_applicable=lambda obj: isinstance(obj, LookupTable),
        template='section.mako')
