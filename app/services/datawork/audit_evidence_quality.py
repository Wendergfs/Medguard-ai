
import glob
import ijson
from collections import Counter

total = 0
with_interactions = 0
with_rxcui = 0
with_ingredients = 0
with_interactions_and_identity = 0
text_lengths = []
examples = []

for path in sorted(glob.glob("drug-label-*.json")):
    with open(path, "rb") as source:
        for record in ijson.items(source, "results.item"):
            total += 1

            interactions = record.get("drug_interactions")
            product = record.get("openfda") or {}

            has_rxcui = bool(product.get("rxcui"))
            has_ingredients = bool(
                record.get("active_ingredient")
                or product.get("substance_name")
                or product.get("generic_name")
            )

            if has_rxcui:
                with_rxcui += 1
            if has_ingredients:
                with_ingredients += 1

            if interactions:
                with_interactions += 1
                text = " ".join(interactions) if isinstance(
                    interactions, list
                ) else str(interactions)
                text_lengths.append(len(text))

                if has_rxcui or has_ingredients:
                    with_interactions_and_identity += 1

                if len(examples) < 5:
                    examples.append({
                        "id": record.get("id"),
                        "rxcui": product.get("rxcui"),
                        "generic_name": product.get("generic_name"),
                        "substance_name": product.get("substance_name"),
                        "interaction_text": text[:800],
                    })

print("Total records:", total)
print("Records with interaction text:", with_interactions)
print("Records with RxCUI:", with_rxcui)
print("Records with ingredient-related identifiers:", with_ingredients)
print("Interaction records with some identity metadata:",
      with_interactions_and_identity)

if text_lengths:
    print("Average interaction text length:",
          round(sum(text_lengths) / len(text_lengths)))
    print("Shortest interaction text:", min(text_lengths))
    print("Longest interaction text:", max(text_lengths))

for i, example in enumerate(examples, 1):
    print(f"\n--- Example {i} ---")
    for key, value in example.items():
        print(f"{key}: {value}")
