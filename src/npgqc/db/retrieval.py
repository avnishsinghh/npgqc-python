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

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from npgqc.db.schema import (
    MqcOutcomeEnt,
    SeqComponent,
    SeqComponentComposition,
    SeqComposition,
)


def get_composition_by_digest(session: Session, digest: str) -> SeqComposition | None:
    """Retrieves a composition by its digest.

    Args:
      session :
        Database session.
      digest :
        A SHA256 hex digest of the JSON representation of the composition.

    Returns:
    -------
      npgqc.db.schema.SeqComposition or None if no composition has this digest.
    """
    return session.execute(
        select(SeqComposition).where(SeqComposition.digest == digest)
    ).scalar_one_or_none()


def get_compositions_by_run(
    session: Session, id_run: int, position: int | None = None
) -> list[SeqComposition]:
    """Retrieves compositions that contain at least one component of a run.

    A composition that merges components from several lanes or runs is
    returned if any of its components matches.

    Args:
      session :
        Database session.
      id_run :
        NPG tracking run ID.
      position :
        Optional lane number. If given, only compositions containing a
        component from this lane are returned.

    Returns:
    -------
      A list of compositions ordered by their primary key.

      An empty list is returned if no composition satisfies the given criteria.
    """
    statement = _compositions_by_run(id_run, position).order_by(
        SeqComposition.id_seq_composition
    )
    return list(session.execute(statement).scalars())


def get_mqc_outcomes_by_run(session: Session, id_run: int) -> list[MqcOutcomeEnt]:
    """Retrieves current sequencing manual QC outcomes for a run.

    Outcomes are found through the components of their compositions, rather
    than the denormalised id_run column of the outcome table, which is optional.

    Args:
      session :
        Database session.
      id_run :
        NPG tracking run ID.

    Returns:
    -------
      A list of outcomes ordered by their composition's primary key.

      An empty list is returned if the run has no outcomes.
    """
    compositions = _compositions_by_run(id_run).subquery()
    statement = (
        select(MqcOutcomeEnt)
        .join(
            compositions,
            MqcOutcomeEnt.id_seq_composition == compositions.c.id_seq_composition,
        )
        .order_by(MqcOutcomeEnt.id_seq_composition)
    )
    return list(session.execute(statement).scalars())


def _compositions_by_run(id_run: int, position: int | None = None) -> Select:
    statement = (
        select(SeqComposition)
        .join(SeqComposition.seq_component_composition)
        .join(SeqComponentComposition.seq_component)
        .where(SeqComponent.id_run == id_run)
    )
    if position is not None:
        statement = statement.where(SeqComponent.position == position)
    return statement.distinct()
