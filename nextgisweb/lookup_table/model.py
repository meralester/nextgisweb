from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import HSTORE

from ..lib import db
from ..env.model import declarative_base
from ..resource import (
    DataScope,
    Resource,
    ResourceGroup,
    ResourceScope,
    Serializer,
    SerializedProperty
)

from .util import _

Base = declarative_base(dependencies=('resource', ))


class LookupTable(Base, Resource):
    identity = 'lookup_table'
    cls_display_name = _("Lookup table")

    __scope__ = DataScope

    val = db.Column(MutableDict.as_mutable(HSTORE))

    @classmethod
    def check_parent(self, parent):
        return isinstance(parent, ResourceGroup)


class _items_attr(SerializedProperty):

    def getter(self, srlzr):
        return srlzr.obj.val

    def setter(self, srlzr, value):
        srlzr.obj.val = value


class LookupTableSerializer(Serializer):
    identity = LookupTable.identity
    resclass = LookupTable

    items = _items_attr(read=ResourceScope.read, write=ResourceScope.update)
