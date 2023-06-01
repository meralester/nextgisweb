from .model import Base
from ..env import Component


class OAPIFServerComponent(Component):
    identity = "oapifserver"
    metadata = Base.metadata

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setup_pyramid(self, config):
        from . import api, view
        api.setup_pyramid(self, config)
        view.setup_pyramid(self, config)
