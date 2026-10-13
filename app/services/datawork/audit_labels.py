import glob
import json
import os
import ijson

files = sorted(glob.glob("drug-label-*.json"))
total = 0

for path in files:
    count = 0
    field_counts = {}
    sample = None

    with open(path, "rb") as f:
        for record in ijson.items(f, "results.item"):
            count += 1

            if sample is None:
                sample = record

            for field in (
                "active_ingredient",
                "warnings",
                "dosage_and_administration",
                "pregnancy_or_breast_feeding",
                "contraindications",
                "drug_interactions",
            ):
                if record.get(field):
                    field_counts[field] = field_counts.get(field, 0) + 1

    total += count
    print(f"\nFile: {os.path.basename(path)}")
    print(f"Records: {count:,}")
    print("Non-empty field counts:", field_counts)

    if sample:
        print("Sample product ID:", sample.get("id"))
        print("Sample active ingredient:", str(sample.get("active_ingredient", []))[:250])
        print("openFDA fields:", list(sample.get("openfda", {}).keys()))

print(f"\nTOTAL RECORDS ACROSS FILES: {total:,}")
