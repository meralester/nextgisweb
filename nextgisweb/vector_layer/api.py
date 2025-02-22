from ..core.exception import ValidationError
from ..lib.ogrhelper import read_dataset
from ..pyramid import JSONType

from .util import _


def dataset(request) -> JSONType:
    source = request.json_body['source']
    datafile, metafile = request.env.file_upload.get_filename(source['id'])
    ogrds = read_dataset(datafile, source_filename=source['name'])
    if ogrds is None:
        raise ValidationError(_("GDAL library failed to open file."))

    layers = []
    for i in range(ogrds.GetLayerCount()):
        layer = ogrds.GetLayer(i)
        layers.append(layer.GetName())

    return dict(layers=layers)


def setup_pyramid(comp, config):
    config.add_route(
        'vector_layer.dataset', '/api/component/vector_layer/dataset'
    ).add_view(dataset, request_method='POST')
