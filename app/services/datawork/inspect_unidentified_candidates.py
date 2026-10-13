
import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "interaction_candidates.jsonl"
OUTPUT_FILE = BASE_DIR / "unidentified_candidates_sample.csv"
SAMPLE_SIZE = 100


def has_value(value):
    if value is None:
        return False
    if isinstance(value, list):
        return any(has_value(item) for item in value)
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def has_structured_identity(record):
    fields = ("rxcui", "generic_name", "substance_name", "brand_name")
    return any(has_value(record.get(field)) for field in fields)


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Cannot find {INPUT_FILE.name}. "
            "Put this script in the same folder as the JSONL file."
        )

    sample = []
    unidentified_count = 0

    with INPUT_FILE.open("r", encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue

            record = json.loads(line)

            if has_structured_identity(record):
                continue

            unidentified_count += 1

            if len(sample) < SAMPLE_SIZE:
                sample.append({
                    "source_record_id": record.get("source_record_id", ""),
                    "effective_time": record.get("effective_time", ""),
                    "matched_class_terms": "; ".join(
                        record.get("matched_class_terms", [])
                    ),
                    "source_text": record.get("source_text", ""),
                    "manual_category": "",
                    "review_notes": "",
                })

    columns = [
        "source_record_id",
        "effective_time",
        "matched_class_terms",
        "source_text",
        "manual_category",
        "review_notes",
    ]

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8-sig"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(sample)

    print("\n========== SAMPLE EXPORT COMPLETE ==========")
    print("Unidentified records found:", f"{unidentified_count:,}")
    print("Sample size exported:", len(sample))
    print("Output file:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
