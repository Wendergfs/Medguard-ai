
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

from flashtext import KeywordProcessor


# --------------------------------------------------
# PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DICTIONARY_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "medication_dictionary"
    / "rxnorm_medication_dictionary.jsonl"
)

# The script checks these common locations.
CANDIDATE_PATHS = [
    PROJECT_ROOT / "data" / "raw" / "openfda" / "interaction_candidates.jsonl",
    PROJECT_ROOT / "app" / "services" / "datawork" / "interaction_candidates.jsonl",
    PROJECT_ROOT / "interaction_candidates.jsonl",
]

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "medication_matches"

OUTPUT_FILE = OUTPUT_DIR / "medication_matches.jsonl"
REPORT_FILE = OUTPUT_DIR / "medication_matching_report.json"


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

# Start with the most useful medication terminology types.
ALLOWED_TERM_TYPES = {
    "IN",       # Ingredient
    "PIN",      # Precise ingredient
    "MIN",      # Multiple ingredients
    "BN",       # Brand name
    "SCD",      # Semantic clinical drug
    "SBD",      # Semantic branded drug
}

MIN_TERM_LENGTH = 3


# --------------------------------------------------
# LOAD RXNORM DICTIONARY
# --------------------------------------------------

def load_rxnorm_dictionary():

    if not DICTIONARY_FILE.exists():
        raise FileNotFoundError(
            f"RxNorm dictionary not found: {DICTIONARY_FILE}"
        )

    term_to_concepts = defaultdict(list)

    with open(DICTIONARY_FILE, "r", encoding="utf-8") as file:

        for line in file:

            record = json.loads(line)

            term = record["name"].strip()
            term_type = record["term_type"]
            rxcui = record["rxcui"]

            if term_type not in ALLOWED_TERM_TYPES:
                continue

            if len(term) < MIN_TERM_LENGTH:
                continue

            if not rxcui:
                continue

            normalized_term = term.lower()

            concept = {
                "rxcui": rxcui,
                "name": term,
                "term_type": term_type,
                "source": record["source"],
            }

            if concept not in term_to_concepts[normalized_term]:
                term_to_concepts[normalized_term].append(concept)

    return term_to_concepts


# --------------------------------------------------
# BUILD SEARCH ENGINE
# --------------------------------------------------

def build_keyword_processor(term_to_concepts):

    processor = KeywordProcessor(case_sensitive=False)

    for term in term_to_concepts:

        processor.add_keyword(term, term)

    return processor


# --------------------------------------------------
# FIND CANDIDATE DATASET
# --------------------------------------------------

def find_candidate_file():

    for path in CANDIDATE_PATHS:

        if path.exists():
            return path

    raise FileNotFoundError(
        "Could not find interaction_candidates.jsonl.\n"
        "Place it in data/raw/openfda/ or update CANDIDATE_PATHS "
        "in medication_matcher.py."
    )


# --------------------------------------------------
# MATCH MEDICATIONS
# --------------------------------------------------

def match_medications():

    print("\nLoading RxNorm terminology...")

    term_to_concepts = load_rxnorm_dictionary()

    print(f"Loaded terminology names: {len(term_to_concepts):,}")

    processor = build_keyword_processor(term_to_concepts)

    print("Medication matching engine ready.")

    input_file = find_candidate_file()

    print(f"\nInput dataset: {input_file}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_passages = 0
    passages_with_matches = 0
    passages_without_matches = 0

    total_mentions = 0
    ambiguous_mentions = 0

    matched_term_types = Counter()

    with open(input_file, "r", encoding="utf-8") as source, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as output:

        for line in source:

            if not line.strip():
                continue

            record = json.loads(line)

            total_passages += 1

            text = record.get("source_text", "")

            if not text:
                passages_without_matches += 1
                continue

            # Return the matched keyword and its character positions.
            found = processor.extract_keywords(
                text,
                span_info=True
            )

            # Remove duplicate occurrences of the same name
            # within one passage, preserving the first occurrence.
            unique_mentions = {}

            for term, start, end in found:

                key = term.lower()

                if key not in unique_mentions:
                    unique_mentions[key] = {
                        "term": term,
                        "start": start,
                        "end": end,
                    }

            medication_mentions = []

            for normalized_term, mention in unique_mentions.items():

                concepts = term_to_concepts[normalized_term]

                # Preserve every possible concept.
                # Never select an arbitrary RxCUI.
                concept_ids = sorted({
                    item["rxcui"] for item in concepts
                })

                is_ambiguous = len(concept_ids) > 1

                if is_ambiguous:
                    ambiguous_mentions += 1

                for item in concepts:
                    matched_term_types[item["term_type"]] += 1

                medication_mentions.append({
                    "matched_text": mention["term"],
                    "start": mention["start"],
                    "end": mention["end"],
                    "concepts": concepts,
                    "rxcuis": concept_ids,
                    "match_status": (
                        "ambiguous"
                        if is_ambiguous
                        else "matched"
                    ),
                })

            if medication_mentions:

                passages_with_matches += 1
                total_mentions += len(medication_mentions)

            else:
                passages_without_matches += 1

            result = {
                "source_record_id": record.get("source_record_id"),
                "effective_time": record.get("effective_time"),
                "source_text": text,
                "medication_mentions": medication_mentions,
                "mention_count": len(medication_mentions),
                "matching_status": (
                    "matched"
                    if medication_mentions
                    else "unmatched"
                ),
            }

            output.write(
                json.dumps(result, ensure_ascii=False) + "\n"
            )

    # --------------------------------------------------
    # REPORT
    # --------------------------------------------------

    report = {
        "input_file": str(input_file),
        "dictionary_file": str(DICTIONARY_FILE),
        "output_file": str(OUTPUT_FILE),
        "total_passages": total_passages,
        "passages_with_matches": passages_with_matches,
        "passages_without_matches": passages_without_matches,
        "passage_match_rate": (
            round(passages_with_matches / total_passages * 100, 2)
            if total_passages else 0
        ),
        "total_unique_mentions_per_passage": total_mentions,
        "ambiguous_mentions": ambiguous_mentions,
        "term_type_matches": dict(matched_term_types),
        "allowed_term_types": sorted(ALLOWED_TERM_TYPES),
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print("\n========== Medication Matching Report ==========")
    print(f"Total passages:          {total_passages:,}")
    print(f"Passages with matches:   {passages_with_matches:,}")
    print(f"Passages without matches:{passages_without_matches:,}")
    print(f"Passage match rate:      {report['passage_match_rate']}%")
    print(f"Medication mentions:     {total_mentions:,}")
    print(f"Ambiguous mentions:      {ambiguous_mentions:,}")

    print("\nTerm type matches:")

    for term_type, count in matched_term_types.most_common():
        print(f"  {term_type}: {count:,}")

    print(f"\nOutput: {OUTPUT_FILE}")
    print(f"Report: {REPORT_FILE}")


if __name__ == "__main__":
    match_medications()
