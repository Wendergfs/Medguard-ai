
import json
from pathlib import Path

files = [
    Path("data/processed/medication_dictionary/rxnorm_medication_dictionary.jsonl"),
    Path("app/services/datawork/interaction_candidates.jsonl"),
    Path("data/processed/medication_matches/medication_matches.jsonl"),
]

for file_path in files:
    print("\n" + "=" * 70)
    print(f"FILE: {file_path}")

    if not file_path.exists():
        print("NOT FOUND")
        continue

    with file_path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                record = json.loads(line)
                print(json.dumps(record, ensure_ascii=False, indent=2)[:3500])
                break
