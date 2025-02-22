from contextlib import contextmanager

from ..env import Component

from .model import Base


class WFSServerComponent(Component):
    identity = 'wfsserver'
    metadata = Base.metadata

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._force_schema_validation = False

    def setup_pyramid(self, config):
        from . import api, view
        api.setup_pyramid(self, config)
        view.setup_pyramid(self, config)

    @contextmanager
    def force_schema_validation(self):
        remember = self._force_schema_validation
        yield
        self._force_schema_validation = remember
