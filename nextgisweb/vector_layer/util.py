from ..lib import db
from ..lib.i18n import trstr_factory
from ..feature_layer import FIELD_TYPE, FIELD_TYPE_OGR, GEOM_TYPE


COMP_ID = 'vector_layer'
_ = trstr_factory(COMP_ID)
SCHEMA = COMP_ID


class ERROR_FIX:
    NONE = 'NONE'
    SAFE = 'SAFE'
    LOSSY = 'LOSSY'

    default = NONE
    enum = (NONE, SAFE, LOSSY)


class FID_SOURCE:
    AUTO = 'AUTO'
    SEQUENCE = 'SEQUENCE'
    FIELD = 'FIELD'


class TOGGLE:
    AUTO = None
    YES = True
    NO = False

    enum = (AUTO, YES, NO)


FIELD_TYPE_2_ENUM = dict(zip(FIELD_TYPE_OGR, FIELD_TYPE.enum))
FIELD_TYPE_DB = (
    db.Integer,
    db.BigInteger,
    db.Float,
    db.Unicode,
    db.Date,
    db.Time,
    db.DateTime)
FIELD_TYPE_2_DB = dict(zip(FIELD_TYPE.enum, FIELD_TYPE_DB))
FIELD_TYPE_SIZE = {
    FIELD_TYPE.INTEGER: 4,
    FIELD_TYPE.BIGINT: 8,
    FIELD_TYPE.REAL: 8,
    FIELD_TYPE.DATE: 4,
    FIELD_TYPE.TIME: 8,
    FIELD_TYPE.DATETIME: 8,
}

GEOM_TYPE_DB = (
    'POINT', 'LINESTRING', 'POLYGON',
    'MULTIPOINT', 'MULTILINESTRING', 'MULTIPOLYGON',
    'POINTZ', 'LINESTRINGZ', 'POLYGONZ',
    'MULTIPOINTZ', 'MULTILINESTRINGZ', 'MULTIPOLYGONZ',
)
GEOM_TYPE_2_DB = dict(zip(GEOM_TYPE.enum, GEOM_TYPE_DB))


def test_encoding(s):
    try:
        s.encode('utf-8')
    except UnicodeEncodeError:
        return False
    else:
        return True


def fix_encoding(s):
    while not test_encoding(s):
        s = s[:-1]
    return s


def utf8len(s):
    return len(s.encode('utf-8'))
