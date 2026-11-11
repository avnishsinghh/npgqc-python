# -*- coding: utf-8 -*-
#
# Copyright © 2026 Genome Research Ltd. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import base64
import os
from pathlib import Path

import pytest
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database, database_exists, drop_database

from npgqc.db.schema import Base

TEST_DB_URL_VAR = "NPGQC_TEST_DB_URL"
FIXTURES_DIR = Path(__file__).parent / "data" / "fixtures"


@pytest.fixture(scope="session")
def mysql_engine():
    """Yields an engine for an empty database with the npg-qc schema."""
    url = os.environ.get(TEST_DB_URL_VAR)
    if not url:
        pytest.skip(f"{TEST_DB_URL_VAR} is not set")

    engine = create_engine(url)
    if database_exists(engine.url):
        drop_database(engine.url)
    create_database(engine.url)
    Base.metadata.create_all(engine)

    yield engine

    drop_database(engine.url)
    engine.dispose()


@pytest.fixture(scope="session")
def loaded_engine(mysql_engine):
    """Yields an engine for a database populated from the YAML fixtures.

    Each file in the fixtures directory is named after a table and holds a
    list of rows. A string value prefixed with "base64:" is decoded to bytes.
    """
    tables = Base.metadata.tables
    with mysql_engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            path = FIXTURES_DIR / f"{table.name}.yml"
            if not path.exists():
                continue
            rows = [_decode_row(row) for row in yaml.safe_load(path.read_text())]
            conn.execute(tables[table.name].insert(), rows)

    yield mysql_engine


@pytest.fixture
def session(loaded_engine):
    """Yields a session that is rolled back after the test."""
    with Session(loaded_engine) as sess:
        yield sess
        sess.rollback()


def _decode_row(row: dict) -> dict:
    return {
        key: base64.b64decode(value[len("base64:") :])
        if isinstance(value, str) and value.startswith("base64:")
        else value
        for key, value in row.items()
    }
