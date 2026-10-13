
import glob
import json
import os
import ijson

OUTPUT = "drug_label_evidence.jsonl"

FIELDS = [
    "active_ingredient",
    "drug_interactions",
    "contraindications",
    "warnings",
    "dosage_and_administration",
    "pregnancy_or_breast_feeding",
]

total = 0
written = 0
seen_ids = set()

with open(OUTPUT, "w", encoding="utf-8") as out:
    for path in sorted(glob.glob("drug-label-*.json")):
        print(f"Processing {os.path.basename(path)}...")

        with open(path, "rb") as source:
            for record in ijson.items(source, "results.item"):
                total += 1
                record_id = record.get("id")

                if not record_id or record_id in seen_ids:
                    continue

                seen_ids.add(record_id)

                evidence = {
                    "record_id": record_id,
                    "effective_time": record.get("effective_time"),
                    "version": record.get("version"),
                    "product": record.get("openfda", {}),
                }

                for field in FIELDS:
                    value = record.get(field)
                    if value:
                        evidence[field] = value

                if any(evidence.get(field) for field in FIELDS):
                    out.write(
                        json.dumps(evidence, ensure_ascii=False) + "\n"
                    )
                    written += 1

        print(f"Records scanned: {total:,}")
        print(f"Evidence records written: {written:,}")

print("\nFinished.")
print(f"Total records scanned: {total:,}")
print(f"Unique IDs found: {len(seen_ids):,}")
print(f"Evidence records written: {written:,}")
print(f"Output file: {os.path.abspath(OUTPUT)}")
