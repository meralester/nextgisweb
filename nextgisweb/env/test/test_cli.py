from ...lib.clann import ArgumentParser
from ...env import Env
from ...core import CoreComponent
from ..cli import bootstrap, cli, EnvCommand


@cli.command()
def do_test(this: EnvCommand, *, env: Env, core: CoreComponent):
    assert env is this.env
    assert core is this.env.core


def test_command(ngw_env):
    args = ['do_test']

    bs_parser = ArgumentParser(bootstrap, add_help=False)
    ns_nspc, _ = bs_parser.parse_known_args(args)
    bs_parser.execute(ns_nspc)

    cli_parser = ArgumentParser(cli)
    cli_nspc = cli_parser.parse_args(args)
    cli_parser.execute(cli_nspc)
