from datetime import timedelta

from ..lib.config import Option
from ..env import Component

from .model import Base, WMS_VERSIONS


class WMSClientComponent(Component):
    identity = 'wmsclient'
    metadata = Base.metadata

    def initialize(self):
        super().initialize()

        self.headers = {
            'User-Agent': self.options['user_agent']
        }

    def setup_pyramid(self, config):
        from . import view
        view.setup_pyramid(self, config)

    def client_settings(self, request):
        return dict(wms_versions=WMS_VERSIONS)

    option_annotations = (
        Option('user_agent', default="NextGIS Web"),
        Option('timeout', timedelta, default=timedelta(seconds=15), doc="WMS request timeout."),
    )
