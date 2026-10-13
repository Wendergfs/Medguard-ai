
import json
from collections import Counter
from pathlib import Path

# Files are expected in the same folder as this script.
BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "interaction_candidates.jsonl"
REPORT_FILE = BASE_DIR / "interaction_audit_report.json"


def has_value(value):
    """Return True if a field contains at least one meaningful value."""
    if value is None:
        return False

    if isinstance(value, list):
        return any(has_value(item) for item in value)

    if isinstance(value, str):
        return bool(value.strip())

    return bool(value)


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Cannot find {INPUT_FILE.name}.\n"
            "Put this script in the same folder as interaction_candidates.jsonl."
        )

    counts = Counter()
    class_counts = Counter()
    source_ids = set()
    duplicate_source_ids = 0
    total_text_chars = 0
    shortest_text = None
    longest_text = 0
    malformed_lines = 0

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                malformed_lines += 1
                continue

            counts["total_candidates"] += 1

            source_id = record.get("source_record_id")
            if source_id:
                if source_id in source_ids:
                    duplicate_source_ids += 1
                else:
                    source_ids.add(source_id)

            rxcui = has_value(record.get("rxcui"))
            generic = has_value(record.get("generic_name"))
            substance = has_value(record.get("substance_name"))
            brand = has_value(record.get("brand_name"))

            if rxcui:
                counts["with_rxcui"] += 1
            if generic:
                counts["with_generic_name"] += 1
            if substance:
                counts["with_substance_name"] += 1
            if brand:
                counts["with_brand_name"] += 1

            has_generic_or_substance = generic or substance
            has_any_identity = rxcui or generic or substance or brand

            if has_any_identity:
                counts["with_any_structured_identity"] += 1
            else:
                counts["with_no_structured_identity"] += 1

            # Mutually exclusive categories:
            if rxcui:
                counts["category_rxcui_present"] += 1
            elif has_generic_or_substance:
                counts["category_generic_or_substance_no_rxcui"] += 1
            elif brand:
                counts["category_brand_only"] += 1
            else:
                counts["category_no_structured_identity"] += 1

            matched_classes = record.get("matched_class_terms", [])
            if isinstance(matched_classes, list):
                for term in matched_classes:
                    if has_value(term):
                        class_counts[str(term)] += 1

                if matched_classes:
                    counts["with_matched_class_terms"] += 1

            text = record.get("source_text", "")
            if not isinstance(text, str):
                text = str(text) if text is not None else ""

            text_length = len(text)
            total_text_chars += text_length

            if shortest_text is None or text_length < shortest_text:
                shortest_text = text_length

            longest_text = max(longest_text, text_length)

            if not text.strip():
                counts["empty_source_text"] += 1

            if counts["total_candidates"] % 10000 == 0:
                print(
                    f"Processed {counts['total_candidates']:,} candidates..."
                )

    total = counts["total_candidates"]

    report = {
        "input_file": INPUT_FILE.name,
        "total_candidates": total,
        "records_with_unique_source_ids": len(source_ids),
        "duplicate_source_id_occurrences": duplicate_source_ids,
        "malformed_json_lines": malformed_lines,
        "identity_field_counts_overlap": {
            "with_rxcui": counts["with_rxcui"],
            "with_generic_name": counts["with_generic_name"],
            "with_substance_name": counts["with_substance_name"],
            "with_brand_name": counts["with_brand_name"],
            "with_any_structured_identity":
                counts["with_any_structured_identity"],
            "with_no_structured_identity":
                counts["with_no_structured_identity"],
        },
        "mutually_exclusive_identity_categories": {
            "rxcui_present": counts["category_rxcui_present"],
            "generic_or_substance_without_rxcui":
                counts["category_generic_or_substance_no_rxcui"],
            "brand_only": counts["category_brand_only"],
            "no_structured_identity":
                counts["category_no_structured_identity"],
        },
        "text_and_class_diagnostics": {
            "with_matched_class_terms":
                counts["with_matched_class_terms"],
            "empty_source_text": counts["empty_source_text"],
            "total_source_text_characters": total_text_chars,
            "average_source_text_characters":
                round(total_text_chars / total, 2) if total else 0,
            "shortest_source_text_characters": shortest_text,
            "longest_source_text_characters": longest_text,
            "matched_class_term_counts": dict(class_counts),
        },
        "notes": [
            "Identity field counts overlap; a record can have multiple fields.",
            "Mutually exclusive categories prioritize RxCUI, then generic/substance, then brand.",
            "Matched class terms only reflect the limited patterns in the extraction script.",
            "This audit measures metadata coverage, not verified drug interactions.",
        ],
    }

    REPORT_FILE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n========== AUDIT COMPLETE ==========")
    print("Total candidates:", f"{total:,}")
    print("With RxCUI:", f"{counts['with_rxcui']:,}")
    print("With generic name:", f"{counts['with_generic_name']:,}")
    print("With substance name:", f"{counts['with_substance_name']:,}")
    print("With brand name:", f"{counts['with_brand_name']:,}")
    print(
        "With any structured identity:",
        f"{counts['with_any_structured_identity']:,}",
    )
    print(
        "With no structured identity:",
        f"{counts['with_no_structured_identity']:,}",
    )
    print(
        "With matched class terms:",
        f"{counts['with_matched_class_terms']:,}",
    )
    print("Duplicate source ID occurrences:", f"{duplicate_source_ids:,}")
    print("Malformed JSON lines:", f"{malformed_lines:,}")
    print("\nReport saved to:", REPORT_FILE)


if __name__ == "__main__":
    main()
