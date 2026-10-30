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

"""Database-free tests of the ORM mapping."""

import pytest
from pytest import mark as m
from sqlalchemy import inspect
from sqlalchemy.orm import configure_mappers

from npgqc.db.schema import Base

MAPPERS = sorted(Base.registry.mappers, key=lambda mp: mp.class_.__name__)
TABLES = sorted(Base.metadata.tables.values(), key=lambda t: t.name)


@m.describe("ORM mapping")
class TestMapping:
    @m.it("Configures all mappers without errors")
    def test_configure_mappers(self):
        configure_mappers()

    @m.it("Maps every table in the metadata to a class")
    def test_tables_mapped(self):
        mapped = {mp.local_table.name for mp in MAPPERS}
        assert mapped == set(Base.metadata.tables)

    @m.it("Has a reciprocal relationship for every back_populates")
    @pytest.mark.parametrize("mapper", MAPPERS, ids=lambda mp: mp.class_.__name__)
    def test_back_populates(self, mapper):
        configure_mappers()
        for rel in mapper.relationships:
            assert rel.back_populates, f"{rel} has no back_populates"
            reverse = rel.mapper.relationships[rel.back_populates]
            assert reverse.back_populates == rel.key
            assert reverse.mapper is mapper

    @m.it("Gives every class a primary key")
    @pytest.mark.parametrize("mapper", MAPPERS, ids=lambda mp: mp.class_.__name__)
    def test_primary_key(self, mapper):
        assert inspect(mapper.class_).primary_key

    @m.it("Has a relationship for every foreign key")
    @pytest.mark.parametrize("mapper", MAPPERS, ids=lambda mp: mp.class_.__name__)
    def test_foreign_key_relationships(self, mapper):
        configure_mappers()
        related = {frozenset(rel.local_columns) for rel in mapper.relationships}
        for fk in mapper.local_table.foreign_key_constraints:
            assert frozenset(fk.columns) in related, f"{fk.name} has no relationship"

    @m.it("Names every foreign key and index")
    @pytest.mark.parametrize("table", TABLES, ids=lambda t: t.name)
    def test_constraint_names(self, table):
        for constraint in [*table.foreign_key_constraints, *table.indexes]:
            assert constraint.name, f"Unnamed {constraint!r} on {table.name}"
