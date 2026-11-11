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

"""Tests of the retrieval functions against a MySQL database, see conftest.py."""

from pytest import mark as m

from npgqc.db.retrieval import (
    get_composition_by_digest,
    get_compositions_by_run,
    get_mqc_lane_outcomes_by_run,
    get_mqc_library_outcomes_by_run,
)

LANE_DIGEST = "a" * 64
PLEX_DIGEST = "b" * 64
PLEX_L1_T5_DIGEST = "c" * 64
PLEX_L2_T4_DIGEST = "d" * 64
ID_RUN = 45678
UNKNOWN_ID_RUN = 99999


@m.describe("Retrieving compositions")
class TestCompositions:
    @m.it("Finds a composition by its digest")
    def test_by_digest(self, session):
        compos = get_composition_by_digest(session, LANE_DIGEST)
        assert compos is not None
        assert compos.size == 2

    @m.it("Returns None for an unknown digest")
    def test_by_unknown_digest(self, session):
        assert get_composition_by_digest(session, "f" * 64) is None

    @m.it("Finds every composition of a run once")
    def test_by_run(self, session):
        digests = [c.digest for c in get_compositions_by_run(session, ID_RUN)]
        assert digests == [
            LANE_DIGEST,
            PLEX_DIGEST,
            PLEX_L1_T5_DIGEST,
            PLEX_L2_T4_DIGEST,
        ]

    @m.it("Narrows compositions of a run to one lane")
    def test_by_run_and_position(self, session):
        digests = [c.digest for c in get_compositions_by_run(session, ID_RUN, 2)]
        assert digests == [LANE_DIGEST, PLEX_L2_T4_DIGEST]

    @m.it("Returns an empty list for an unknown run")
    def test_by_unknown_run(self, session):
        assert get_compositions_by_run(session, UNKNOWN_ID_RUN) == []


@m.describe("Retrieving lane manual QC outcomes")
class TestMqcLaneOutcomes:
    @m.it("Finds the lane outcomes of a run")
    def test_by_run(self, session):
        outcomes = get_mqc_lane_outcomes_by_run(session, ID_RUN)
        assert len(outcomes) == 1
        assert outcomes[0].seq_composition.digest == LANE_DIGEST
        assert outcomes[0].mqc_outcome_dict.short_desc == "Accepted final"

    @m.it("Returns an empty list for an unknown run")
    def test_by_unknown_run(self, session):
        assert get_mqc_lane_outcomes_by_run(session, UNKNOWN_ID_RUN) == []


@m.describe("Retrieving library manual QC outcomes")
class TestMqcLibraryOutcomes:
    @m.it("Finds the library outcomes of a run across its lanes")
    def test_by_run(self, session):
        outcomes = get_mqc_library_outcomes_by_run(session, ID_RUN)
        assert [
            (
                o.seq_composition.digest,
                o.position,
                o.tag_index,
                o.mqc_library_outcome_dict.short_desc,
            )
            for o in outcomes
        ] == [
            (PLEX_DIGEST, 1, 3, "Accepted final"),
            (PLEX_L1_T5_DIGEST, 1, 5, "Rejected final"),
            (PLEX_L2_T4_DIGEST, 2, 4, "Accepted preliminary"),
        ]

    @m.it("Returns an empty list for an unknown run")
    def test_by_unknown_run(self, session):
        assert get_mqc_library_outcomes_by_run(session, UNKNOWN_ID_RUN) == []
