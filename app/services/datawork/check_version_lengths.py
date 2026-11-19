
import json
from pathlib import Path

file_path = Path("app/services/datawork/interaction_candidates.jsonl")

max_length = 0
longest_values = []

with file_path.open("r", encoding="utf-8") as file:
    for line_number, line in enumerate(file, start=1):
        record = json.loads(line)
        version = str(record.get("version") or "")

        if len(version) > max_length:
            max_length = len(version)
            longest_values = [(line_number, version)]

        elif len(version) == max_length and len(version) > 20:
            longest_values.append((line_number, version))

print("Maximum version length:", max_length)
print("Examples:")
for line_number, value in longest_values[:10]:
    print(f"Line {line_number}: {value!r}")
