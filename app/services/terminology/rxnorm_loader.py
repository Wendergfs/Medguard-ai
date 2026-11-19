
import csv
import json
from pathlib import Path
from collections import Counter

# Project root: Medguard-ai/
PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "rxnorm" / "RXNCONSO.RRF"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "medication_dictionary"

OUTPUT_JSONL = OUTPUT_DIR / "rxnorm_medication_dictionary.jsonl"
OUTPUT_REPORT = OUTPUT_DIR / "rxnorm_loader_report.json"


def load_rxnorm():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"RXNCONSO.RRF not found: {INPUT_FILE}\n"
            "Check your RxNorm extraction directory."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    accepted_rows = 0
    skipped_rows = 0

    tty_counts = Counter()
    unique_concepts = set()
    unique_names = set()

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
        errors="replace",
        newline=""
    ) as source, open(
        OUTPUT_JSONL,
        "w",
        encoding="utf-8"
    ) as output:

        reader = csv.reader(source, delimiter="|")

        for row in reader:
            total_rows += 1

            # RXNCONSO.RRF contains 18 fields.
            if len(row) < 18:
                skipped_rows += 1
                continue

            rxcui = row[0].strip()
            language = row[1].strip()
            term_status = row[2].strip()
            preferred = row[6].strip()
            source_vocab = row[11].strip()
            term_type = row[12].strip()
            term = row[14].strip()
            suppress = row[16].strip()

            # Keep English, non-suppressed terms with identifiers.
            if (
                language != "ENG"
                or suppress == "Y"
                or not rxcui
                or not term
            ):
                skipped_rows += 1
                continue

            record = {
                "rxcui": rxcui,
                "name": term,
                "term_type": term_type,
                "source": source_vocab,
                "term_status": term_status,
                "is_preferred": preferred == "Y"
            }

            output.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

            accepted_rows += 1
            unique_concepts.add(rxcui)
            unique_names.add(term.lower())
            tty_counts[term_type] += 1

    report = {
        "input_file": str(INPUT_FILE),
        "output_file": str(OUTPUT_JSONL),
        "total_rows": total_rows,
        "accepted_rows": accepted_rows,
        "skipped_rows": skipped_rows,
        "unique_rxcui_count": len(unique_concepts),
        "unique_name_count": len(unique_names),
        "term_type_counts": dict(tty_counts)
    }

    with open(OUTPUT_REPORT, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print("\n========== RxNorm Loader Report ==========")
    print(f"Total rows:          {total_rows:,}")
    print(f"Accepted rows:       {accepted_rows:,}")
    print(f"Skipped rows:        {skipped_rows:,}")
    print(f"Unique RxCUIs:       {len(unique_concepts):,}")
    print(f"Unique names:        {len(unique_names):,}")
    print(f"\nDictionary: {OUTPUT_JSONL}")
    print(f"Report:     {OUTPUT_REPORT}")
    print("\nTerm types:")

    for term_type, count in tty_counts.most_common():
        print(f"  {term_type}: {count:,}")


if __name__ == "__main__":
    load_rxnorm()
