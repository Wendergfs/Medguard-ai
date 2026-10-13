
import glob
import ijson

total = 0
empty = 0
whitespace_only = 0
missing_identity = 0
examples = []

for path in sorted(glob.glob("drug-label-*.json")):
    with open(path, "rb") as source:
        for record in ijson.items(source, "results.item"):
            value = record.get("drug_interactions")

            if not value:
                continue

            total += 1
            text = " ".join(value) if isinstance(value, list) else str(value)

            if text == "":
                empty += 1
            elif not text.strip():
                whitespace_only += 1

            product = record.get("openfda") or {}
            identity = (
                product.get("rxcui")
                or product.get("substance_name")
                or product.get("generic_name")
                or product.get("brand_name")
                or record.get("active_ingredient")
            )

            if not identity:
                missing_identity += 1
                if len(examples) < 5:
                    examples.append({
                        "id": record.get("id"),
                        "text": text[:300],
                    })

print("Records with truthy interaction fields:", total)
print("Empty strings:", empty)
print("Whitespace-only text:", whitespace_only)
print("No identity fields at all:", missing_identity)
print("\nExamples without identity:")
for item in examples:
    print(item)
