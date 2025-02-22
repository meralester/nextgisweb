import os
import os.path
from datetime import datetime
from pathlib import Path

import sqlalchemy as sa
import transaction
from sqlalchemy.dialects import postgresql, sqlite
from zope.sqlalchemy import mark_changed

from ..lib.config import Option
from ..lib.logging import logger
from ..env import Component, require
from ..core import KindOfData
from ..env.model import DBSession

from .model import Base, ResourceTileCache as RTC, TIMESTAMP_EPOCH
from .util import _


vacuum_freepage_coeff = 0.5


class TileCacheData(KindOfData):
    identity = 'tile_cache'
    display_name = _("Tile cache")


class RenderComponent(Component):
    identity = 'render'
    metadata = Base.metadata

    def initialize(self):
        opt_tcache = self.options.with_prefix('tile_cache')
        self.tile_cache_enabled = opt_tcache['enabled']
        self.tile_cache_track_changes = opt_tcache['track_changes']
        self.tile_cache_seed = opt_tcache['seed']

        self.tile_cache_path = os.path.join(self.env.core.gtsdir(self), 'tile_cache')
        if not os.path.isdir(self.tile_cache_path):
            os.makedirs(self.tile_cache_path)

    @require('resource')
    def setup_pyramid(self, config):
        from . import api, view # NOQA
        api.setup_pyramid(self, config)
        view.setup_pyramid(self, config)

    def client_settings(self, request):
        return dict(tile_cache=dict(
            enabled=self.tile_cache_enabled,
            track_changes=self.tile_cache_track_changes,
            seed=self.tile_cache_seed
        ))

    def sys_info(self):
        from .imgcodec import has_fpng
        yield ("Fast PNG", _("Enabled") if has_fpng else _("Disabled"))

    def maintenance(self):
        self.cleanup()

    def cleanup(self):
        logger.info("Cleaning up tile cache tables...")

        root = Path(self.tile_cache_path)
        deleted_tiles = deleted_files = deleted_tables = 0

        with transaction.manager:
            for row in DBSession.execute(sa.text('''
                SELECT t.tablename
                FROM pg_catalog.pg_tables t
                LEFT JOIN resource_tile_cache r
                    ON replace(r.uuid::character varying, '-', '') = t.tablename::character varying
                WHERE t.schemaname = 'tile_cache' AND r.resource_id IS NULL
            ''')):
                tablename = row[0]
                db_path = root / tablename[0:2] / tablename[2:4] / tablename
                if db_path.exists():
                    db_path.unlink()
                    deleted_files += 1
                DBSession.execute(sa.text('DROP TABLE "tile_cache"."%s"' % tablename))
                deleted_tables += 1

            if deleted_tables > 0:
                mark_changed(DBSession())

        now_unix = int((datetime.utcnow() - TIMESTAMP_EPOCH).total_seconds())

        with transaction.manager:
            conn_pg = DBSession.connection()

            for tc in RTC.filter(
                sa.or_(RTC.ttl.isnot(None), RTC.max_z.isnot(None))
            ).all():
                cond = []
                if tc.max_z is not None:
                    cond.append(sa.column('z') > tc.max_z)
                if tc.ttl is not None:
                    cond.append(sa.column('tstamp') < now_unix - tc.ttl)

                where = sa.or_(*cond)

                def statement(dialect, table, schema=None):
                    table = sa.sql.table(table)
                    table.quote = True
                    if schema is not None:
                        table.schema = schema
                        table.quote_schema = True
                    stmt = table.delete().where(where)
                    return stmt.compile(dialect=dialect, compile_kwargs=dict(literal_binds=True))

                stmt = statement(postgresql.dialect(), tc.uuid.hex, 'tile_cache')
                result = conn_pg.execute(stmt)
                deleted_tiles += result.rowcount

                stmt2 = statement(sqlite.dialect(), 'tile')
                conn_sqlite, lock = tc.get_tilestor()

                with lock:
                    result = conn_sqlite.execute(str(stmt2))
                    conn_sqlite.commit()
                    deleted_tiles += result.rowcount

                    freelist_count, page_count = conn_sqlite.execute(
                        'SELECT fc.freelist_count, pc.page_count '
                        'FROM pragma_freelist_count fc, pragma_page_count pc;').fetchone()

                    if page_count > 0 and (freelist_count / page_count > vacuum_freepage_coeff):
                        logger.info('VACUUM database %s...' % tc.tilestor_path)
                        conn_sqlite.execute('VACUUM;')

            mark_changed(DBSession())

        logger.info(
            "Deleted: %d tile records, %d files, %d tables.",
            deleted_tiles, deleted_files, deleted_tables)

    def backup_configure(self, config):
        super().backup_configure(config)
        config.exclude_table_data('tile_cache', '*')

    def estimate_storage(self):
        for tc in RTC.filter_by(enabled=True).all():
            tilestor, lock = tc.get_tilestor()
            query_tile = 'SELECT coalesce(sum(length(data) + 16), 0) FROM tile'  # with 4x int columns
            size_img = tilestor.execute(query_tile).fetchone()[0]

            query = sa.text('SELECT count(1) FROM tile_cache."{}"'.format(tc.uuid.hex))
            count = DBSession.execute(query).scalar()
            size_color = count * 20  # 5x int columns

            yield TileCacheData, tc.resource_id, size_img + size_color

    option_annotations = (
        Option('check_origin', bool, default=False, doc="Check request Origin header."),
        Option('tile_cache.enabled', bool, default=True),
        Option('tile_cache.track_changes', bool, default=False),
        Option('tile_cache.seed', bool, default=False),
        Option('legend_symbols_section', bool, default=False),
    )
