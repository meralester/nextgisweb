import io
import os
import re

from collections import OrderedDict
from shutil import copyfileobj

from ..lib import db
from ..env import env
from ..env.model import declarative_base
from ..resource import Resource
from ..file_storage import FileObj

Base = declarative_base(dependencies=('resource', 'feature_layer'))


KEYNAME_RE = re.compile(r'[a-z_][a-z0-9_]*', re.IGNORECASE)


class FeatureAttachment(Base):
    __tablename__ = 'feature_attachment'

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.ForeignKey(Resource.id), nullable=False)
    feature_id = db.Column(db.Integer, nullable=False)
    keyname = db.Column(db.Unicode, nullable=True)
    fileobj_id = db.Column(db.ForeignKey(FileObj.id), nullable=False)

    name = db.Column(db.Unicode, nullable=True)
    size = db.Column(db.BigInteger, nullable=False)
    mime_type = db.Column(db.Unicode, nullable=False)

    description = db.Column(db.Unicode, nullable=True)

    fileobj = db.relationship(FileObj, lazy='joined')

    resource = db.relationship(Resource, backref=db.backref(
        '__feature_attachment', cascade='all'))

    __table_args__ = (
        db.Index('feature_attachment_resource_id_feature_id_idx', resource_id, feature_id),
        db.UniqueConstraint(
            resource_id, feature_id, keyname,
            deferrable=True, initially='DEFERRED',
            name="feature_attachment_keyname_unique",
        ),
    )

    @property
    def is_image(self):
        return self.mime_type in ('image/jpeg', 'image/png')

    @db.validates('keyname')
    def _validate_keyname(self, key, value):
        if value is None or KEYNAME_RE.match(value):
            return value
        raise ValueError

    def serialize(self):
        return OrderedDict((
            ('id', self.id), ('name', self.name), ('keyname', self.keyname),
            ('size', self.size), ('mime_type', self.mime_type),
            ('description', self.description),
            ('is_image', self.is_image)))

    def deserialize(self, data):
        file_upload = data.get('file_upload')
        if file_upload is not None:
            self.fileobj = env.file_storage.fileobj(
                component='feature_attachment')

            srcfile, _ = env.file_upload.get_filename(file_upload['id'])
            dstfile = env.file_storage.filename(self.fileobj, makedirs=True)

            with io.open(srcfile, 'rb') as fs, io.open(dstfile, 'wb') as fd:
                copyfileobj(fs, fd)

            for k in ('name', 'mime_type'):
                if k in file_upload:
                    setattr(self, k, file_upload[k])

            self.size = os.stat(dstfile).st_size

        for k in ('name', 'keyname', 'mime_type', 'description'):
            if k in data:
                setattr(self, k, data[k])
