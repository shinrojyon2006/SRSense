#!/usr/bin/env python3
"""
A7 - Invalid Graph Data Repair Script
Removes false-positive AI-generated dependency relationships caused by A6 bug.
Only removes suggestions/relationships where original_req_id is NOT a valid structured ID.
Valid IDs: FR-001, NFR-002, REQ-12, US-014 (uppercase prefix + hyphen + digits)
Invalid: User, System, Admin (ordinary words)

Usage:
  cd backend
  python ../scripts/repair_invalid_graph_data.py          # dry-run
  python ../scripts/repair_invalid_graph_data.py --execute # actually delete
"""

import asyncio
import re
import sys
import argparse

sys.path.insert(0, ".")

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.suggestion import RequirementSuggestion, SuggestionStatus
from app.models.relationship import RequirementRelationship, RelationshipType
from app.models.requirement import Requirement

VALID_REQ_ID_PATTERN = re.compile(r"^[A-Z]{1,5}-\d{1,5}$")


def is_invalid_req_id(raw_id: str) -> bool:
    return not VALID_REQ_ID_PATTERN.match(raw_id.strip())


async def repair(dry_run: bool = True):
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    deleted_suggestions = 0
    deleted_relationships = 0

    print("=" * 70)
    print("SRSense A7 - Invalid Graph Data Repair Script")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else '*** EXECUTE (WILL DELETE) ***'}")
    print("=" * 70)

    async with async_session() as db:
        print("\n[Step 1] Checking RequirementSuggestion records...\n")
        all_sugs = (await db.execute(
            select(RequirementSuggestion).where(
                RequirementSuggestion.relationship_type == RelationshipType.DEPENDS_ON,
                RequirementSuggestion.status == SuggestionStatus.SUGGESTED,
            )
        )).scalars().all()

        false_positive_sug_ids = []
        for sug in all_sugs:
            target = (await db.execute(
                select(Requirement).where(Requirement.id == sug.target_id)
            )).scalar_one_or_none()
            if not target:
                continue
            raw_id = (target.original_req_id or "").strip()
            if not raw_id or not is_invalid_req_id(raw_id):
                continue
            source = (await db.execute(
                select(Requirement).where(Requirement.id == sug.source_id)
            )).scalar_one_or_none()
            if source and raw_id.lower() in source.description.lower():
                print(f"  [FALSE POSITIVE SUGGESTION] {sug.id}")
                print(f"    Source: '{source.title}'")
                print(f"    Target: '{target.title}'")
                print(f"    Bad ID: '{raw_id}' -- not a valid structured ID")
                print(f"    Action: {'WOULD DELETE' if dry_run else 'DELETING'}\n")
                false_positive_sug_ids.append(sug.id)

        print(f"  Found {len(false_positive_sug_ids)} false-positive suggestion(s).")
        if not dry_run and false_positive_sug_ids:
            await db.execute(
                delete(RequirementSuggestion).where(
                    RequirementSuggestion.id.in_(false_positive_sug_ids)
                )
            )
            await db.commit()
            deleted_suggestions = len(false_positive_sug_ids)

        print("\n[Step 2] Checking RequirementRelationship records...\n")
        all_rels = (await db.execute(
            select(RequirementRelationship).where(
                RequirementRelationship.type == RelationshipType.DEPENDS_ON,
            )
        )).scalars().all()

        false_positive_rel_ids = []
        for rel in all_rels:
            meta = rel.metadata_json or {}
            if "accepted_from_suggestion_id" not in meta:
                continue  # User-created -- preserve
            target = (await db.execute(
                select(Requirement).where(Requirement.id == rel.target_id)
            )).scalar_one_or_none()
            if not target:
                continue
            raw_id = (target.original_req_id or "").strip()
            if not raw_id or not is_invalid_req_id(raw_id):
                continue
            source = (await db.execute(
                select(Requirement).where(Requirement.id == rel.source_id)
            )).scalar_one_or_none()
            if source and raw_id.lower() in source.description.lower():
                print(f"  [FALSE POSITIVE RELATIONSHIP] {rel.id}")
                print(f"    Source: '{source.title}'")
                print(f"    Target: '{target.title}'")
                print(f"    Bad ID: '{raw_id}' -- not a valid structured ID")
                print(f"    Action: {'WOULD DELETE' if dry_run else 'DELETING'}\n")
                false_positive_rel_ids.append(rel.id)

        print(f"  Found {len(false_positive_rel_ids)} false-positive relationship(s).")
        if not dry_run and false_positive_rel_ids:
            await db.execute(
                delete(RequirementRelationship).where(
                    RequirementRelationship.id.in_(false_positive_rel_ids)
                )
            )
            await db.commit()
            deleted_relationships = len(false_positive_rel_ids)

    await engine.dispose()
    print("\n" + "=" * 70)
    print("REPAIR SUMMARY")
    print(f"  False-positive suggestions:   {len(false_positive_sug_ids)}")
    print(f"  False-positive relationships: {len(false_positive_rel_ids)}")
    if dry_run:
        print("\n  [DRY RUN] No changes made. Run with --execute to apply.")
    else:
        print(f"\n  Deleted suggestions:   {deleted_suggestions}")
        print(f"  Deleted relationships: {deleted_relationships}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="SRSense A7 - Invalid Graph Data Repair")
    parser.add_argument("--execute", action="store_true",
                        help="Actually delete false-positive records (default is dry-run).")
    args = parser.parse_args()
    asyncio.run(repair(dry_run=not args.execute))


if __name__ == "__main__":
    main()
