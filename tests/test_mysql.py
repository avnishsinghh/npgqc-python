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

"""Tests of the ORM against a MySQL database, see conftest.py."""

import datetime
from decimal import Decimal

from pytest import mark as m
from sqlalchemy import select

from npgqc.db.schema import (
    Generic,
    MqcOutcomeEnt,
    SamtoolsStats,
    SeqComponent,
    SeqComposition,
    SequenceSummary,
    SplitStats,
    VerifyBamId,
)

LANE_DIGEST = "a" * 64
PLEX_DIGEST = "b" * 64


@m.describe("Querying through the ORM")
class TestQuery:
    @m.it("Links a composition to its components")
    def test_composition_components(self, session):
        compos = session.execute(
            select(SeqComposition).where(SeqComposition.digest == LANE_DIGEST)
        ).scalar_one()

        components = [cc.seq_component for cc in compos.seq_component_composition]
        assert compos.size == len(components) == 2
        assert sorted((c.id_run, c.position) for c in components) == [
            (45678, 1),
            (45678, 2),
        ]

    @m.it("Links a component back to its compositions")
    def test_component_compositions(self, session):
        component = session.execute(
            select(SeqComponent).where(SeqComponent.tag_index == 3)
        ).scalar_one()

        digests = [cc.seq_composition.digest for cc in component.seq_component_composition]
        assert digests == [PLEX_DIGEST]

    @m.it("Retrieves a manual QC outcome with its dictionary entry")
    def test_mqc_outcome(self, session):
        outcome = session.execute(
            select(MqcOutcomeEnt).join(SeqComposition).where(
                SeqComposition.digest == LANE_DIGEST
            )
        ).scalar_one()

        assert outcome.mqc_outcome_dict.short_desc == "Accepted final"
        assert outcome.seq_composition.mqc_outcome_ent == [outcome]
        assert isinstance(outcome.last_modified, datetime.datetime)

    @m.it("Round-trips binary data in a LONGBLOB column")
    def test_longblob(self, session):
        stats = session.execute(
            select(SamtoolsStats).where(SamtoolsStats.filter == "F0x900")
        ).scalar_one()

        assert stats.stats == b"\x1f\x8b\x08\x00compressed"
        assert stats.seq_composition.digest == PLEX_DIGEST

    @m.it("Applies server defaults on insert")
    def test_server_defaults(self, session):
        compos = session.execute(
            select(SeqComposition).where(SeqComposition.digest == PLEX_DIGEST)
        ).scalar_one()
        summary = SequenceSummary(
            seq_composition=compos,
            sequence_format="CRAM",
            header="@HD\tVN:1.6",
            seqchksum="1",
            seqchksum_sha512="2",
            md5="c" * 32,
        )
        session.add(summary)
        session.flush()
        session.refresh(summary)

        assert summary.iscurrent == 1
        assert isinstance(summary.date, datetime.datetime)

    @m.it("Deserialises JSON columns to Python objects")
    def test_json(self, session):
        generic = session.execute(
            select(Generic).where(Generic.pp_name == "ncov2019-artic-nf")
        ).scalar_one()

        assert generic.doc == {
            "meta": {"sample_type": "positive_control", "num_input_reads": 102394},
            "QC summary": {
                "pct_N_bases": 1.67,
                "qc_pass": True,
                "lineages": ["B.1.1.7", "B.1.617.2"],
            },
        }
        assert generic.info["Check_version"] == "72.1.0"
        assert generic.seq_composition.digest == PLEX_DIGEST

    @m.it("Returns DECIMAL columns as exact Decimal values")
    def test_decimal(self, session):
        verify = session.execute(
            select(VerifyBamId).join(SeqComposition).where(
                SeqComposition.digest == PLEX_DIGEST
            )
        ).scalar_one()

        assert verify.freemix == Decimal("0.00123")
        assert verify.avg_depth == Decimal("15.75")
        assert isinstance(verify.freemix, Decimal)
        assert verify.pass_ == 1

    @m.it("Links split stats to their per-chromosome coverage")
    def test_split_stats_coverage(self, session):
        stats = session.execute(
            select(SplitStats).join(SeqComposition).where(
                SeqComposition.digest == LANE_DIGEST
            )
        ).scalar_one()

        coverage = sorted(stats.split_stats_coverage, key=lambda c: c.chromosome)
        assert [(c.chromosome, c.coverage) for c in coverage] == [
            ("11", 0.5),
            ("MT", 1.25),
        ]
        assert all(c.split_stats is stats for c in coverage)
