import os
import sys
from os.path import join as path_join
from os.path import split as path_split
from os.path import exists as path_exists
from typing import Optional
from datetime import datetime
from contextlib import contextmanager
from tempfile import TemporaryDirectory, mkdtemp, mkstemp
from shutil import rmtree
from zipfile import ZipFile, is_zipfile

from ...lib.logging import logger
from ...cli import cli, EnvCommand, opt, arg

from .. import backup as mod


@cli.command()
def backup(
    self: EnvCommand,
    no_zip: bool = opt(False),
    target: Optional[str] = arg(metavar="path"),
):
    """Backup data into an archive
    
    :param no_zip: Don't compress a backup with ZIP
    :param target: Output file or directory"""

    opts = self.env.core.options.with_prefix('backup')

    if target is None:
        base_path = opts['path']
        if base_path is None:
            raise RuntimeError("Default backup path (core.backup.path) isn't set")
        autoname = datetime.today().strftime(opts['filename'])
        target = path_join(base_path, autoname)

    to_stdout = target == '-'

    tmp_root = opts.get('tmpdir', None if to_stdout else path_split(target)[0])

    if not to_stdout and path_exists(target):
        raise RuntimeError("Target already exists!")

    if no_zip:
        @contextmanager
        def tgt_context():
            tmpdir = mkdtemp(dir=tmp_root)
            try:
                yield tmpdir
                logger.debug("Renaming [%s] to [%s]...", tmpdir, target)
                os.rename(tmpdir, target)
            except Exception:
                rmtree(tmpdir)
                raise

    elif to_stdout:
        @contextmanager
        def tgt_context():
            with TemporaryDirectory(dir=tmp_root) as tmp_dir:
                yield tmp_dir
                _compress(tmp_dir, sys.stdout.buffer)
    else:
        @contextmanager
        def tgt_context():
            with TemporaryDirectory(dir=tmp_root) as tmp_dir:
                yield tmp_dir
                tmp_arch = mkstemp(dir=tmp_root)[1]
                os.unlink(tmp_arch)
                try:
                    _compress(tmp_dir, tmp_arch)
                    logger.debug("Renaming [%s] to [%s]...", tmp_arch, target)
                    os.rename(tmp_arch, target)
                except Exception:
                    os.unlink(tmp_arch)
                    raise

    with tgt_context() as tgt:
        mod.backup(self.env, tgt)

    if not to_stdout:
        print(target)


@cli.command()
def restore(self: EnvCommand, source: str = arg(metavar='path')):
    """Restore data from a backup
    
    :param path: Path to a backup"""

    opts = self.env.core.options.with_prefix('backup')

    source = self.source
    from_stdin = source == '-'
    if from_stdin:
        @contextmanager
        def src_context():
            tmp_root = opts.get('tmpdir', None)
            with TemporaryDirectory(dir=tmp_root) as tmpdir:
                _decompress(sys.stdin.buffer, tmpdir)
                yield tmpdir
    elif is_zipfile(source):
        @contextmanager
        def src_context():
            tmp_root = opts.get('tmpdir', path_split(source)[0])
            with TemporaryDirectory(dir=tmp_root) as tmpdir:
                _decompress(source, tmpdir)
                yield tmpdir
    else:
        @contextmanager
        def src_context():
            yield source

    with src_context() as src:
        mod.restore(self.env, src)


def _compress(src, dst):
    logger.debug(
        "Compressing '%s' to '%s'...", src,
        dst if isinstance(dst, str) else dst.name)
    with ZipFile(dst, 'w', allowZip64=True) as zipf:
        for root, dirs, files in os.walk(src):
            zipf.write(root, os.path.relpath(root, src))
            for fn in files:
                filename = path_join(root, fn)
                if os.path.isfile(filename):
                    arcname = path_join(os.path.relpath(root, src), fn)
                    zipf.write(filename, arcname)
                    os.unlink(filename)  # Free space as soon as possible


def _decompress(src, dst):
    logger.debug(
        "Decompressing '%s' to '%s'...",
        src if isinstance(src, str) else src.name, dst)
    with ZipFile(src, 'r') as zipf:
        zipf.extractall(dst)
