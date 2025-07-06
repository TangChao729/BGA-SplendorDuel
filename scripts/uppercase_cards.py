"""
Script to normalize 'color' and 'ability' fields in cards.json to uppercase.
"""

import json
import os


def main():
    base = os.path.dirname(os.path.dirname(__file__))
    cards_path = os.path.join(base, "data", "cards.json")
    with open(cards_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for level_key, cards in data.items():
        for card in cards:
            # Uppercase color
            if "color" in card and isinstance(card["color"], str):
                card["color"] = card["color"].upper()
            # Uppercase ability if not None
            if "ability" in card and isinstance(card["ability"], str):
                card["ability"] = card["ability"].upper()

    # Backup original
    backup_path = cards_path + ".bak"
    os.replace(cards_path, backup_path)
    with open(cards_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Normalized cards.json; backup saved to {backup_path}")


if __name__ == "__main__":
    main()
