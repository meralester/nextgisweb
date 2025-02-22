import sys
from typing import Optional

import transaction

from ...lib.clann import command, group, opt
from ...lib.config import load_config
from ..environment import Env, env, inject
from .. import environment


class EnvOptions:
    config: Optional[str] = opt(metavar="path", doc="Configuration file path")


class DryRunOptions:
    no_dry_run: bool = opt(False, doc="Make changes (no changes by default)")

    @property
    def dry_run(self):
        return not self.no_dry_run


@command()
class bootstrap(EnvOptions):

    def __enter__(self):
        pass

    def __call__(self):
        if environment._env is None:
            Env(cfg=load_config(self.config, None, hupper=True), set_global=True)

        assert environment._env is not None

        # Scan for {component_module}.cli modules to populate commands
        for comp in env.components.values():
            candidate = f'{comp.module}.cli'
            if candidate not in sys.modules:
                try:
                    __import__(candidate)
                except ModuleNotFoundError:
                    pass

    def __exit__(self, type, value, traceback):
        pass


class EnvCommand(EnvOptions):
    env: Optional[Env] = None
    env_initialize: bool = True
    use_transaction: bool = False

    @classmethod
    def customize(cls, **kwargs):
        return type('CustomCommand', (cls, ), kwargs)

    def __enter__(self):
        self.env = environment._env

        if self.env_initialize:
            self.env.initialize()

        if self.use_transaction:
            assert self.env_initialize
            transaction.manager.__enter__()

    def __call__(self):
        pass

    def __exit__(self, type, value, traceback):
        if self.use_transaction:
            transaction.manager.__exit__(type, value, traceback)


@group(decorator=inject())
class cli(EnvOptions):
    pass
