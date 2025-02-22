from collections import defaultdict

import pytest

from ...env import load_all
from .. import Resource


def pytest_generate_tests(metafunc):
    if 'resource_cls' in metafunc.fixturenames:
        load_all()
        metafunc.parametrize('resource_cls', [
            pytest.param(cls, id=cls.identity)
            for cls in Resource.registry])


def test_requirement_ordering(resource_cls):
    requirements = resource_cls.class_requirements()

    dependencies = defaultdict(set)
    for req in requirements:
        dependencies[req.dst].add(req)

    for req in requirements:
        if req.attr is None:
            assert len(dependencies[req.src]) == 0, "{} evaluated before {}".format(
                req, tuple(dependencies[req.src]))
        dependencies[req.dst].remove(req)
