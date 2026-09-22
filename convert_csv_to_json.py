"""
Convert a spreadsheet of Hebrew words (CSV) into the words.json format
used by the flashcard app.

Usage:
    python convert_csv_to_json.py words.csv words.json

CSV columns required (header row, in any order):
    id        - unique slug, e.g. "kelev"
    image     - path to the PNG, e.g. "assets/kelev.png"
    letters   - the word's letters in READING order, separated by spaces
                e.g. "כ ל ב"
    translit  - transliteration shown after a correct answer
    gloss     - English gloss shown after a correct answer
"""

import csv
import json
import sys
import unicodedata
from pathlib import Path

REQUIRED_COLUMNS = {"id", "image", "letters", "translit", "gloss"}


def strip_niqqud(text: str) -> str:
    """Remove vowel points / cantillation marks, keeping consonants only."""
    decomposed = unicodedata.normalize("NFD", text)
    consonants_only = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", consonants_only)


def convert(csv_path: Path, json_path: Path) -> None:
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            sys.exit(f"CSV is missing required column(s): {', '.join(sorted(missing))}")

        words = []
        seen_ids = set()
        errors = []

        for row_num, row in enumerate(reader, start=2):  # row 1 is the header
            word_id = row["id"].strip()
            # Strip any vowel points/cantillation and normalize, so consonants
            # come out identical regardless of whether the source was typed
            # by hand or copy-pasted from a fully pointed text.
            letters = [
                strip_niqqud(token)
                for token in row["letters"].strip().split()
            ]

            if not word_id:
                errors.append(f"Row {row_num}: missing id")
                continue
            if word_id in seen_ids:
                errors.append(f"Row {row_num}: duplicate id '{word_id}'")
                continue
            if not letters:
                errors.append(f"Row {row_num} ('{word_id}'): no letters found")
                continue

            seen_ids.add(word_id)
            words.append({
                "id": word_id,
                "image": row["image"].strip(),
                "letters": letters,
                "translit": row["translit"].strip(),
                "gloss": row["gloss"].strip(),
            })

        if errors:
            print("Found problems — fix these rows and re-run:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Wrote {len(words)} word(s) to {json_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python convert_csv_to_json.py <input.csv> <output.json>")
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
