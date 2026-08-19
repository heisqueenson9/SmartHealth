#!/usr/bin/env python3
"""
Run this ONCE locally, wherever data/Final_Augmented_dataset_Diseases_and_Symptoms.csv
actually exists on disk (it's gitignored, so this won't run on Render).
It reads only the header row — not the 246,945 data rows — and writes a
small, git-committable JSON vocabulary file that seed.py loads on every
deploy. The huge CSV itself never needs to exist in production.

Usage:
    python scripts/extract_symptom_vocabulary.py
"""

import csv
import json
import re
from pathlib import Path

SOURCE_CSV = Path(__file__).resolve().parent.parent / "data" / "Final_Augmented_dataset_Diseases_and_Symptoms.csv"
OUTPUT_JSON = Path(__file__).resolve().parent.parent / "backend" / "database" / "symptom_vocabulary.json"

LABEL_COLUMNS = {"diseases", "disease", "label"}

CATEGORY_KEYWORDS = {
    "Cardiovascular": ["chest", "heart", "palpitation", "pulse", "cardiac"],
    "Respiratory": ["breath", "cough", "wheeze", "lung", "congestion"],
    "Gastrointestinal": ["stomach", "abdominal", "nausea", "vomit", "diarrhea", "bowel", "appetite"],
    "Neurological": ["headache", "dizz", "seizure", "numbness", "confusion", "memory", "vision"],
    "Musculoskeletal": ["joint", "muscle", "back pain", "swelling", "stiffness"],
    "Dermatological": ["rash", "itch", "skin", "lesion"],
    "Hematological": ["bleed", "bruis", "pale", "anemia", "clot"],
    "Metabolic": ["weight", "thirst", "urination", "fatigue", "sweat"],
    "Psychiatric": ["anxiety", "depress", "mood", "sleep", "insomnia"],
}


def guess_category(name: str) -> str:
    lowered = name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return category
    return "General"


def to_code(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return f"SYM_{slug.upper()}"


def to_display_name(column_name: str) -> str:
    words = re.sub(r"[_\-]+", " ", column_name).strip().split()
    return " ".join(w.capitalize() for w in words)


def main():
    if not SOURCE_CSV.exists():
        raise SystemExit(f"Dataset not found at {SOURCE_CSV}. Run this where the CSV lives locally.")

    with open(SOURCE_CSV, "r", encoding="utf-8") as fh:
        header = next(csv.reader(fh))

    symptom_columns = [c for c in header if c.strip().lower() not in LABEL_COLUMNS]
    vocabulary, seen = [], set()

    for col in symptom_columns:
        display_name = to_display_name(col)
        code = to_code(col)
        if not display_name or code in seen:
            continue
        seen.add(code)
        vocabulary.append({
            "code": code,
            "display_name": display_name,
            "category": guess_category(display_name),
            "synonyms": [],
            "description": None,
        })

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(vocabulary, fh, indent=2)

    print(f"Wrote {len(vocabulary)} symptom vocabulary entries to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
