from sqlalchemy import *                    # NOQA
from sqlalchemy.orm import *                # NOQA

from sqlalchemy import event                # NOQA
from sqlalchemy import sql                  # NOQA
from sqlalchemy import func                 # NOQA
from sqlalchemy import types                # NOQA

from sqlalchemy import Enum as _Enum
from sqlalchemy.dialects.postgresql import UUID as _UUID, JSONB  # NOQA


class Enum(_Enum):
    """ sqlalchemy.Enum wrapped with native_enum=False pre-installed"""

    def __init__(self, *args, **kwargs):
        for k, v in (
            ('native_enum', False),
            ('create_constraint', False),
            ('validate_strings', True),
        ):
            if k in kwargs:
                assert kwargs[k] == v
            else:
                kwargs[k] = v

        if 'length' not in kwargs:
            kwargs['length'] = 50

        super().__init__(*args, **kwargs)


class UUID(_UUID):
    """ SQLAclhemy-s PostgreSQL UUID wrapper with as_uuid=True by default """

    def __init__(self, *args, **kwargs):
        if 'as_uuid' not in kwargs:
            kwargs['as_uuid'] = True
        super().__init__(*args, **kwargs)
