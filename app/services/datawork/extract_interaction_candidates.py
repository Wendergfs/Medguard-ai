
import glob
import json
import os
import re
import ijson

OUTPUT = "interaction_candidates.jsonl"

# Diagnostic patterns only. Expand and validate against a
# medication terminology source before relying on these results.
CLASS_PATTERNS = {
    "CYP3A4 inhibitor": r"\bCYP3A4 inhibitors?\b",
    "CYP3A4 inducer": r"\bCYP3A4 inducers?\b",
    "benzodiazepines": r"\bbenzodiazepines?\b",
    "nitrates": r"\bnitrates?\b",
    "alpha-blockers": r"\balpha[- ]blockers?\b",
    "anthracyclines": r"\banthracyclines?\b",
}

compiled = {
    name: re.compile(pattern, re.IGNORECASE)
    for name, pattern in CLASS_PATTERNS.items()
}

records_scanned = 0
candidates_written = 0

with open(OUTPUT, "w", encoding="utf-8") as out:
    for path in sorted(glob.glob("drug-label-*.json")):
        print("Processing:", os.path.basename(path))

        with open(path, "rb") as source:
            for record in ijson.items(source, "results.item"):
                records_scanned += 1

                raw = record.get("drug_interactions")
                if not raw:
                    continue

                text = " ".join(raw) if isinstance(raw, list) else str(raw)
                text = text.strip()

                if not text:
                    continue

                product = record.get("openfda") or {}

                matches = [
                    name for name, pattern in compiled.items()
                    if pattern.search(text)
                ]

                candidate = {
                    "source_record_id": record.get("id"),
                    "effective_time": record.get("effective_time"),
                    "version": record.get("version"),
                    "brand_name": product.get("brand_name", []),
                    "generic_name": product.get("generic_name", []),
                    "rxcui": product.get("rxcui", []),
                    "substance_name": product.get("substance_name", []),
                    "matched_class_terms": matches,
                    "source_text": text,
                    "extraction_status": "unreviewed",
                }

                out.write(json.dumps(candidate, ensure_ascii=False) + "\n")
                candidates_written += 1

print("\nExtraction finished.")
print("Source records scanned:", records_scanned)
print("Candidate passages written:", candidates_written)
print("Output:", os.path.abspath(OUTPUT))
