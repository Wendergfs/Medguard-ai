import glob
import ijson
from collections import Counter

seen_ids = set()
duplicate_ids = Counter()
total = 0
missing_ids = 0
interaction_records = 0
samples_printed = 0

for path in sorted(glob.glob("drug-label-*.json")):
    with open(path, "rb") as f:
        for record in ijson.items(f, "results.item"):
            total += 1

            record_id = record.get("id")
            if record_id:
                if record_id in seen_ids:
                    duplicate_ids[record_id] += 1
                else:
                    seen_ids.add(record_id)
            else:
                missing_ids += 1

            interactions = record.get("drug_interactions")
            if interactions:
                interaction_records += 1

                if samples_printed < 5:
                    print("\n--- INTERACTION EXAMPLE ---")
                    print("File:", path)
                    print("Record ID:", record_id)
                    print("Product:", record.get("openfda", {}).get("brand_name"))
                    print("Ingredient:", str(record.get("active_ingredient", []))[:300])
                    print("Interaction text:", str(interactions)[:1200])
                    samples_printed += 1

print("\n========== AUDIT SUMMARY ==========")
print("Total records:", total)
print("Unique non-empty IDs:", len(seen_ids))
print("IDs occurring more than once:", len(duplicate_ids))
print("Extra duplicate occurrences:", sum(duplicate_ids.values()))
print("Records missing IDs:", missing_ids)
print("Records with interaction text:", interaction_records)
