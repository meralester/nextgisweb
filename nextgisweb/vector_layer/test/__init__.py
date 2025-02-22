from contextlib import contextmanager
from uuid import uuid4

import transaction

from ...auth import User
from ...env.model import DBSession
from ...spatial_ref_sys import SRS

from .. import VectorLayer


@contextmanager
def create_feature_layer(ogrlayer, parent_id, **kwargs):
    with transaction.manager:
        layer = VectorLayer(
            parent_id=parent_id, display_name='Feature layer (vector)',
            owner_user=User.by_keyname('administrator'),
            srs=SRS.filter_by(id=3857).one(),
            tbl_uuid=uuid4().hex,
        ).persist()

        layer.setup_from_ogr(ogrlayer)
        layer.load_from_ogr(ogrlayer)

        DBSession.flush()

    yield layer
