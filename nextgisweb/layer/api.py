from ..resource import DataScope, resource_factory
from ..pyramid import JSONType
from .interface import IBboxLayer


def extent(resource, request) -> JSONType:
    request.resource_permission(DataScope.read)

    return dict(extent=resource.extent)


def setup_pyramid(comp, config):
    config.add_route(
        'layer.extent', '/api/resource/{id}/extent',
        factory=resource_factory) \
        .add_view(extent, context=IBboxLayer, request_method='GET')
