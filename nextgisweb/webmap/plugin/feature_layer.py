from pyramid import threadlocal

from ...feature_layer import IFeatureLayer, IFeatureQueryLike
from ...resource import DataScope
from .base import WebmapLayerPlugin


@WebmapLayerPlugin.registry.register
class FeatureLayerPlugin(WebmapLayerPlugin):

    @classmethod
    def is_layer_supported(cls, layer, webmap):
        if IFeatureLayer.providedBy(layer):
            request = threadlocal.get_current_request()
            return ("ngw-webmap/plugin/FeatureLayer", dict(
                readonly=not layer.has_permission(DataScope.write, request.user),
                likeSearch=IFeatureQueryLike.providedBy(layer.feature_query())
            ))
