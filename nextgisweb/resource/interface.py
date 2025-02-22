import zope.interface
from zope.interface import implements


class IResourceBase(zope.interface.Interface):
    pass


def providedBy(obj):
    for i in zope.interface.providedBy(obj):
        if issubclass(i, IResourceBase) and i != IResourceBase:
            yield i
