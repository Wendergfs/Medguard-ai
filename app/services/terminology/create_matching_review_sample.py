
import json
import csv
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "medication_matches"
    / "medication_matches.jsonl"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "medication_matches"

OUTPUT_FILE = OUTPUT_DIR / "matching_review_sample.csv"

SAMPLE_SIZE = 100
RANDOM_SEED = 42


def create_review_sample():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    records = []

    print("Loading matching results...")

    with open(INPUT_FILE, "r", encoding="utf-8") as file:

        for line in file:

            if not line.strip():
                continue

            record = json.loads(line)
            records.append(record)

    random.seed(RANDOM_SEED)

    sample_size = min(SAMPLE_SIZE, len(records))

    sample = random.sample(records, sample_size)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "source_record_id",
                "source_text",
                "matched_text",
                "rxcui",
                "term_type",
                "match_status",
                "manual_correct",
                "correct_medication",
                "review_notes"
            ]
        )

        writer.writeheader()

        for record in sample:

            mentions = record.get("medication_mentions", [])

            if not mentions:

                writer.writerow({
                    "source_record_id": record.get("source_record_id"),
                    "source_text": record.get("source_text"),
                    "matched_text": "",
                    "rxcui": "",
                    "term_type": "",
                    "match_status": "unmatched",
                    "manual_correct": "",
                    "correct_medication": "",
                    "review_notes": ""
                })

            else:

                for mention in mentions:

                    for concept in mention.get("concepts", []):

                        writer.writerow({
                            "source_record_id": record.get("source_record_id"),
                            "source_text": record.get("source_text"),
                            "matched_text": mention.get("matched_text"),
                            "rxcui": concept.get("rxcui"),
                            "term_type": concept.get("term_type"),
                            "match_status": mention.get("match_status"),
                            "manual_correct": "",
                            "correct_medication": "",
                            "review_notes": ""
                        })

    print("\n========== Review Sample ==========")
    print(f"Passages sampled: {sample_size}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    create_review_sample()
