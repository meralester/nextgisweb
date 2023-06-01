from datetime import datetime
from pyramid.httpexceptions import HTTPNotFound
from shapely.geometry import box

from .model import Service
from ..lib.geometry import Geometry
from ..feature_layer.api import query_feature_or_not_found, serialize
from ..pyramid import JSONType
from ..resource import resource_factory, ServiceScope
from ..spatial_ref_sys import SRS


CONFORMANCE = [
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
]


def collection_to_ogc(collection, request):
    extent = collection.resource.extent
    return dict(
        links=[
            {
                "rel": "self",
                "type": "application/json",
                "title": "This document",
                "href": request.route_url(
                    "oapifserver.collection",
                    id=collection.service.id,
                    collection_id=collection.keyname,
                ),
            },
            {
                "rel": "items",
                "type": "application/geo+json",
                "title": "items as GeoJSON",
                "href": request.route_url(
                    "oapifserver.items",
                    id=collection.service.id,
                    collection_id=collection.keyname,
                ),
            },
        ],
        id=collection.keyname,
        title=collection.display_name,
        description=collection.resource.description,
        itemType="feature",
        extent={
            "spatial": {
                "bbox": (
                    extent["minLon"],
                    extent["minLat"],
                    extent["maxLon"],
                    extent["maxLat"],
                ),
                "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84",
            }
        },
    )


def feature_to_ogc(feature):
    result = serialize(feature, geom_format="geojson", dt_format="iso")
    return dict(
        type="Feature",
        geometry=result["geom"],
        properties=result["fields"],
    )


def conformance(request) -> JSONType:
    return dict(conformsTo=CONFORMANCE)


def landing_page(resource, request) -> JSONType:
    request.resource_permission(ServiceScope.connect)

    def route_url(rname):
        return request.route_url(rname, id=resource.id)

    return dict(
        title=resource.display_name,
        description=resource.description,
        links=[
            {
                "rel": "self",
                "type": "application/json",
                "title": "This document",
                "href": route_url("oapifserver.landing_page"),
            },
            {
                "rel": "conformance",
                "type": "application/json",
                "title": "Conformance",
                "href": route_url("oapifserver.conformance"),
            },
            {
                "rel": "data",
                "type": "application/json",
                "title": "Collections",
                "href": route_url("oapifserver.collections"),
            },
            {
                "rel": "service-desc",
                "type": "application/vnd.oai.openapi+json;version=3.0",
                "title": "The OpenAPI definition",
                "href": route_url("oapifserver.openapi")
            }
        ],
    )


def collections(resource, request) -> JSONType:
    request.resource_permission(ServiceScope.connect)
    collections = [collection_to_ogc(c, request) for c in resource.collections]
    return dict(
        collections=collections,
        links=[
            {
                "rel": "self",
                "type": "application/json",
                "title": "This document",
                "href": request.route_url("oapifserver.collections", id=resource.id),
            }
        ],
    )


def collection(resource, request) -> JSONType:
    request.resource_permission(ServiceScope.connect)
    collection_id = request.matchdict["collection_id"]
    for c in resource.collections:
        if c.keyname == collection_id:
            return collection_to_ogc(c, request)
    raise HTTPNotFound()


def items(resource, request) -> JSONType:
    request.resource_permission(ServiceScope.connect)
    collection_id = request.matchdict["collection_id"]
    for c in resource.collections:
        if c.keyname == collection_id:
            limit = (
                int(limit)
                if (limit := request.GET.get("limit", c.maxfeatures)) is not None
                else 10
            )
            offset = int(request.GET.get("offset", 0))
            query = c.resource.feature_query()
            query.srs(SRS.filter_by(id=4326).one())
            query.geom()
            query.limit(limit, offset)
            
            bbox = request.GET.get("bbox")
            if bbox is not None:
                box_coords = map(float, bbox.split(",")[:4])
                box_geom = Geometry.from_shape(box(*box_coords), srid=4326, validate=False)
                query.intersects(box_geom)

            features = [feature_to_ogc(feature) for feature in query()]

            items = dict(
                type="FeatureCollection",
                features=features,
                timeStamp=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                links=[
                    {
                        "rel": "self",
                        "type": "application/json",
                        "title": "This document",
                        "href": request.route_url(
                            "oapifserver.items",
                            id=resource.id,
                            collection_id=collection_id,
                            _query=request.params
                        ),
                    },
                    {
                        "rel": "next",
                        "type": "application/geo+json",
                        "title": "items (next)",
                        "href": request.route_url(
                            "oapifserver.items",
                            id=resource.id,
                            collection_id=collection_id,
                            _query={**request.params, "offset": limit + offset},
                        ),
                    },
                    {
                        "rel": "collection",
                        "type": "application/json",
                        "title": c.display_name,
                        "href": request.route_url(
                            "oapifserver.collection",
                            id=resource.id,
                            collection_id=collection_id,
                        ),
                    },
                ],
            )
            return items
    return HTTPNotFound()


def item(resource, request) -> JSONType:
    request.resource_permission(ServiceScope.connect)
    collection_id = request.matchdict["collection_id"]
    item_id = int(request.matchdict["item_id"])
    for c in resource.collections:
        if c.keyname == collection_id:
            query = c.resource.feature_query()
            query.srs(SRS.filter_by(id=4326).one())
            query.geom()
            feature = query_feature_or_not_found(query, c.resource.id, item_id)
            item = feature_to_ogc(feature)
            item["links"] = [
                {
                    "rel": "self",
                    "type": "application/geo+json",
                    "title": "This document",
                    "href": request.route_url(
                        "oapifserver.item",
                        id=resource.id,
                        collection_id=collection_id,
                        item_id=item_id,
                    ),
                },
                {
                    "rel": "collection",
                    "type": "application/json",
                    "title": c.display_name,
                    "href": request.route_url(
                        "oapifserver.collection",
                        id=resource.id,
                        collection_id=collection_id,
                    ),
                },
            ]
            return item
    raise HTTPNotFound()


def openapi(request) -> JSONType:
    # https://github.com/MapServer/MapServer/blob/db74212ec9d16030870bc4a280771febfada8091/mapogcapi.cpp#L1382
    # https://github.com/geopython/pygeoapi/blob/master/pygeoapi/openapi.py
    return {}


def setup_pyramid(comp, config):
    config.add_route(
        "oapifserver.openapi", r"/api/resource/{id:\d+}/oapif/openapi",
        factory=resource_factory) \
        .add_view(openapi, context=Service, request_method="GET")
    config.add_route(
        "oapifserver.landing_page", r"/api/resource/{id:\d+}/oapif/",
        factory=resource_factory) \
        .add_view(landing_page, context=Service, request_method="GET")
    config.add_route(
        "oapifserver.conformance", r"/api/resource/{id:\d+}/oapif/conformance",
        factory=resource_factory
        ).add_view(conformance, context=Service, request_method="GET")
    config.add_route(
        "oapifserver.collections", r"/api/resource/{id:\d+}/oapif/collections",
        factory=resource_factory) \
        .add_view(collections, context=Service, request_method="GET")
    config.add_route(
        "oapifserver.collection", r"/api/resource/{id:\d+}/oapif/collections/{collection_id}",
        factory=resource_factory) \
        .add_view(collection, context=Service, request_method="GET")
    config.add_route(
        "oapifserver.items", r"/api/resource/{id:\d+}/oapif/collections/{collection_id}/items",
        factory=resource_factory) \
        .add_view(items, context=Service, request_method="GET")
    config.add_route(
        "oapifserver.item", r"/api/resource/{id:\d+}/oapif/collections/{collection_id}/items/{item_id:\d+}",
        factory=resource_factory) \
        .add_view(item, context=Service, request_method="GET")
