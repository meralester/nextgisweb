from collections import UserList
from functools import reduce

from bunch import Bunch


class RequirementList(UserList):

    def toposort(self):
        g = dict()
        for a in self:
            g[a] = set()
            for b in self:
                if a.src == b.dst and a != b:
                    g[a].add(b)

        self[:] = []

        extra = reduce(set.union, g.values(), set()) - set(g.keys())
        g.update({item: set() for item in extra})

        while True:
            ordered = set(item for item, dep in g.items() if not dep)
            if not ordered:
                break

            self.extend(ordered)

            g = {item: (dep - ordered)
                 for item, dep in g.items()
                 if item not in ordered}

        assert not g, "A cyclic dependency exists amongst %r" % g


class Requirement:

    def __init__(self, dst, src, attr=None, cls=None, attr_empty=False):
        self.dst = dst
        self.src = src
        self.attr = attr
        self.cls = cls
        self.attr_empty = attr_empty

    def __repr__(self):
        return '<Requirement: %s requires %s on attr=%s>' % (
            repr(self.dst), repr(self.src), self.attr)


class Permission:

    # Counter to number objects. Needed to get elements in
    # a way they were created inside class.
    __create_order = 0

    def __init__(self, label=None, name=None, scope=None):
        self.label = label
        self.name = name
        self.scope = scope

        if not self.is_bound():
            self._requirements = list()

        Permission.__create_order += 1
        self._create_order = Permission.__create_order

    def __repr__(self):
        return "<Permission %s:%s>" % (self.scope.identity if self.scope else '*', self.name)

    def __str__(self):
        return str(self.label)

    def is_bound(self):
        return self.name is not None and self.scope is not None

    def bind(self, name=None, scope=None):
        self.name = name
        self.scope = scope

        self.scope.requirements.extend(self._requirements)
        self.scope.requirements.toposort()
        del self._requirements

    def require(self, *args, **kwargs):
        tgt = self.scope.requirements \
            if self.is_bound() \
            else self._requirements

        tgt.append(Requirement(self, *args, **kwargs))

        if self.is_bound():
            tgt.toposort()

        return self


class ScopeMeta(type):

    def __init__(cls, classname, bases, nmspc):
        Scope = globals().get('Scope', None)

        assert Scope is None or 'identity' in cls.__dict__, \
            'Attribute identity not found in %s' % classname

        if Scope is not None:
            setattr(cls, 'requirements', RequirementList())

        for name, perm in cls.__dict__.items():
            if not isinstance(perm, Permission):
                continue

            perm.bind(name, cls)

        super().__init__(classname, bases, nmspc)

        if Scope is not None:
            cls.registry[cls.__dict__['identity']] = cls

    __registry = Bunch()

    @property
    def registry(cls):
        return cls.__registry

    def values(cls, ordered=False):
        def _ordered(a):
            return sorted(a, key=lambda i: i._create_order) \
                if ordered else a

        for v in _ordered(filter(
            lambda v: isinstance(v, Permission),
            cls.__dict__.values()
        )):
            yield v

    # NOTE: Backward compability
    itervalues = values


class Scope(metaclass=ScopeMeta):
    pass
