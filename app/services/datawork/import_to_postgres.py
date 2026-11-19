
import json
from pathlib import Path

from sqlalchemy import select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.database import engine
from app.models import (
    Medication,
    MedicationTerm,
    EvidencePassage,
    MedicationMention,
)


ROOT = Path(__file__).resolve().parents[3]

RXNORM_FILE = ROOT / "data/processed/medication_dictionary/rxnorm_medication_dictionary.jsonl"
CANDIDATES_FILE = ROOT / "app/services/datawork/interaction_candidates.jsonl"
MATCHES_FILE = ROOT / "data/processed/medication_matches/medication_matches.jsonl"

BATCH_SIZE = 1000


def read_batches(path, batch_size=BATCH_SIZE):
    batch = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                batch.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON in {path}, line {line_number}"
                ) from error

            if len(batch) >= batch_size:
                yield batch
                batch = []

    if batch:
        yield batch


def execute_insert(session, model, rows, constraint):
    if not rows:
        return

    statement = insert(model).values(rows)
    statement = statement.on_conflict_do_nothing(
        constraint=constraint
    )

    session.execute(statement)


# --------------------------------------------------
# 1. RXNORM
# --------------------------------------------------

def import_rxnorm(session):
    print("\n[1/3] Importing RxNorm...")

    total_rows = 0
    concept_count = 0
    term_count = 0

    for batch in read_batches(RXNORM_FILE):
        total_rows += len(batch)

        concepts = {}
        terms = {}

        for record in batch:
            rxcui = record.get("rxcui")
            name = record.get("name")

            if not rxcui or not name:
                continue

            rxcui = str(rxcui)

            if rxcui not in concepts:
                concepts[rxcui] = {
                    "rxcui": rxcui,
                    "preferred_name": name,
                }

            elif record.get("is_preferred"):
                concepts[rxcui]["preferred_name"] = name

            term_key = (
                rxcui,
                name,
                record.get("term_type"),
                record.get("source"),
            )

            terms[term_key] = {
                "rxcui": rxcui,
                "name": name,
                "term_type": record.get("term_type"),
                "source": record.get("source"),
                "term_status": record.get("term_status"),
                "is_preferred": bool(record.get("is_preferred")),
            }

        execute_insert(
            session,
            Medication,
            list(concepts.values()),
            "medications_pkey",
        )

        execute_insert(
            session,
            MedicationTerm,
            list(terms.values()),
            "uq_medication_term",
        )

        concept_count += len(concepts)
        term_count += len(terms)

        session.commit()

        if total_rows % 10000 < BATCH_SIZE:
            print(f"RxNorm rows processed: {total_rows:,}")

    print(f"RxNorm rows read: {total_rows:,}")
    print(f"Unique concepts prepared: {concept_count:,}")
    print(f"Terms prepared: {term_count:,}")


# --------------------------------------------------
# 2. FDA EVIDENCE
# --------------------------------------------------

def import_evidence(session):
    print("\n[2/3] Importing FDA evidence...")

    total = 0
    prepared = 0

    for batch in read_batches(CANDIDATES_FILE):
        rows = []

        for record in batch:
            source_id = record.get("source_record_id")
            source_text = record.get("source_text")

            if not source_id or not source_text:
                continue

            rows.append({
                "source_record_id": source_id,
                "effective_time": record.get("effective_time"),
                "version": record.get("version"),
                "source_text": source_text,
                "extraction_status": record.get(
                    "extraction_status", "unreviewed"
                ),
                "source_metadata": {
                    "brand_name": record.get("brand_name", []),
                    "generic_name": record.get("generic_name", []),
                    "rxcui": record.get("rxcui", []),
                    "substance_name": record.get("substance_name", []),
                    "matched_class_terms": record.get(
                        "matched_class_terms", []
                    ),
                },
            })

        execute_insert(
            session,
            EvidencePassage,
            rows,
            "uq_evidence_source_version",
        )

        total += len(batch)
        prepared += len(rows)

        session.commit()

        if total % 10000 < BATCH_SIZE:
            print(f"Evidence records processed: {total:,}")

    print(f"Evidence records read: {total:,}")
    print(f"Evidence records prepared: {prepared:,}")


# --------------------------------------------------
# 3. MEDICATION MENTIONS
# --------------------------------------------------

def import_mentions(session):
    print("\n[3/3] Importing medication mentions...")

    # Load the 82k unique RxCUIs once instead of querying
    # the database for every medication mention.
    valid_rxcuis = set(
        session.scalars(select(Medication.rxcui)).all()
    )

    total_passages = 0
    total_mentions = 0
    missing_passages = 0
    missing_medications = 0

    for batch in read_batches(MATCHES_FILE):

        passage_keys = {
            (
                record.get("source_record_id"),
                record.get("effective_time"),
            )
            for record in batch
            if record.get("source_record_id")
        }

        if not passage_keys:
            continue

        query = select(
            EvidencePassage.source_record_id,
            EvidencePassage.effective_time,
            EvidencePassage.id,
        ).where(
            tuple_(
                EvidencePassage.source_record_id,
                EvidencePassage.effective_time,
            ).in_(list(passage_keys))
        )

        passage_map = {
            (row.source_record_id, row.effective_time): row.id
            for row in session.execute(query)
        }

        mention_rows = []

        for record in batch:
            total_passages += 1

            key = (
                record.get("source_record_id"),
                record.get("effective_time"),
            )

            passage_id = passage_map.get(key)

            if passage_id is None:
                missing_passages += 1
                continue

            for mention in record.get("medication_mentions", []):
                matched_text = mention.get("matched_text")

                for concept in mention.get("concepts", []):
                    rxcui = str(concept.get("rxcui", ""))

                    if not rxcui or not matched_text:
                        continue

                    if rxcui not in valid_rxcuis:
                        missing_medications += 1
                        continue

                    mention_rows.append({
                        "passage_id": passage_id,
                        "rxcui": rxcui,
                        "matched_text": matched_text,
                        "start": mention.get("start"),
                        "end": mention.get("end"),
                        "term_type": concept.get("term_type"),
                        "match_status": mention.get("match_status"),
                    })

        execute_insert(
            session,
            MedicationMention,
            mention_rows,
            "uq_medication_mention",
        )

        total_mentions += len(mention_rows)

        session.commit()

        if total_passages % 10000 < BATCH_SIZE:
            print(
                f"Matched passages processed: {total_passages:,}"
            )

    print(f"Matched passages processed: {total_passages:,}")
    print(f"Mentions prepared: {total_mentions:,}")
    print(f"Missing passages: {missing_passages:,}")
    print(f"Missing medication concepts: {missing_medications:,}")


# --------------------------------------------------
# DATABASE SUMMARY
# --------------------------------------------------

def print_summary(session):
    print("\n========== DATABASE SUMMARY ==========")

    for name, model in [
        ("Medications", Medication),
        ("Medication terms", MedicationTerm),
        ("Evidence passages", EvidencePassage),
        ("Medication mentions", MedicationMention),
    ]:
        count = session.query(model).count()
        print(f"{name}: {count:,}")

    print("=======================================")


def main():
    for path in [
        RXNORM_FILE,
        CANDIDATES_FILE,
        MATCHES_FILE,
    ]:
        if not path.exists():
            raise FileNotFoundError(path)

    print("Starting MedGuard AI import...")

    with Session(engine) as session:
        try:
            import_rxnorm(session)
            import_evidence(session)
            import_mentions(session)
            print_summary(session)

        except Exception:
            session.rollback()
            raise

    print("\nImport completed!")


if __name__ == "__main__":
    main()
