import pytest
import sqlalchemy as sa
import transaction
from sqlalchemy.engine.url import (
    URL as EngineURL,
    make_url as make_engine_url)

from ...auth import User
from ...env.model import DBSession
from ...spatial_ref_sys import SRS

from .. import PostgisConnection, PostgisLayer
from ..diagnostics import StatusEnum


@pytest.fixture()
def creds(ngw_env):
    opts_db = ngw_env.core.options.with_prefix('test.database')

    for o in ('host', 'name', 'user'):
        if o not in opts_db:
            pytest.skip(f"Option test.database.{o} isn't set")

    con_args = dict(
        host=opts_db['host'],
        port=opts_db['port'],
        database=opts_db['name'],
        username=opts_db['user'],
        password=opts_db['password'])

    engine_url = make_engine_url(EngineURL.create(
        'postgresql+psycopg2', **con_args))
    engine = sa.create_engine(engine_url)

    with engine.connect() as conn:
        with conn.begin():
            conn.execute(sa.text('''
                CREATE TABLE test_types
                (
                    id bigserial PRIMARY KEY,
                    geom geometry(Point,3857),
                    fld_varchar character varying, fld_character character(50), fld_text text, fld_uuid uuid,
                    fld_int integer, fld_bigint bigint,
                    fld_double double precision, fld_numeric numeric,
                    fld_date date, fld_time_without_tz time without time zone, fld_ts_without_tz timestamp without time zone
                );

                INSERT INTO test_types (
                    geom,
                    fld_varchar, fld_character, fld_text, fld_uuid,
                    fld_int, fld_bigint,
                    fld_double, fld_numeric,
                    fld_date, fld_time_without_tz, fld_ts_without_tz
                )
                VALUES (
                    ST_SetSRID('POINT (0 0)'::geometry, 3857),
                    'varchar', 'character', 'text', md5(random()::text)::uuid,
                    -1, 9223372036854775807,
                    1.1, 1.2,
                    now(), now(), now()
                );
            '''))

        try:
            yield con_args
        finally:
            with conn.begin():
                conn.execute(sa.text('DROP TABLE test_types;'))


def test_types(creds, ngw_resource_group, ngw_webtest_app, ngw_auth_administrator):
    with transaction.manager:
        admin = User.by_keyname('administrator')

        connection = PostgisConnection(
            parent_id=ngw_resource_group, owner_user=admin,
            display_name='Test types connection',
            hostname=creds['host'], port=creds['port'],
            database=creds['database'], username=creds['username'],
            password=creds['password']
        ).persist()

        layer = PostgisLayer(
            parent_id=ngw_resource_group, owner_user=admin,
            display_name='Test types layer',
            connection=connection, srs=SRS.filter_by(id=3857).one(),
            schema='public', table='test_types', column_id='id', column_geom='geom',
        ).persist()

        layer.setup()

        DBSession.flush()

    resp = ngw_webtest_app.post_json('/api/component/postgis/check', dict(layer=dict(id=layer.id)))
    assert StatusEnum(resp.json['status']) is StatusEnum.SUCCESS
