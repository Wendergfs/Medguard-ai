
import glob
import ijson
import re
from collections import Counter

patterns = {
    "brand_or_named_drug": re.compile(
        r"\b(?:Kerendia|tadalafil|PHESGO|Tegretol|Thorazine)\b",
        re.IGNORECASE,
    ),
    "drug_class": re.compile(
        r"\b(?:CYP3A4 inhibitors|benzodiazepines|"
        r"alpha-blockers|anthracyclines|nitrates)\b",
        re.IGNORECASE,
    ),
}

counts = Counter()
examples = {key: [] for key in patterns}

for path in sorted(glob.glob("drug-label-*.json")):
    with open(path, "rb") as source:
        for record in ijson.items(source, "results.item"):
            interaction = record.get("drug_interactions")
            if not interaction:
                continue

            text = " ".join(interaction) if isinstance(
                interaction, list
            ) else str(interaction)

            if not text.strip():
                continue

            product = record.get("openfda") or {}
            identity = (
                product.get("rxcui")
                or product.get("substance_name")
                or product.get("generic_name")
                or product.get("brand_name")
                or record.get("active_ingredient")
            )

            if identity:
                continue

            counts["unidentified_interaction_records"] += 1

            for label, pattern in patterns.items():
                if pattern.search(text):
                    counts[label] += 1
                    if len(examples[label]) < 5:
                        examples[label].append({
                            "record_id": record.get("id"),
                            "matched_text": pattern.findall(text)[:5],
                            "passage": text[:500],
                        })

print("Counts:", dict(counts))
for label, items in examples.items():
    print(f"\n--- {label} ---")
    for item in items:
        print(item)
