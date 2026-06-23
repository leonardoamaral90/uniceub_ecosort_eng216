from __future__ import annotations

from typing import Dict, List

RECYCLABLE_CLASSES = {"metal", "glass", "paper", "cardboard", "plastic"}
NON_RECYCLABLE_CLASSES = {"biological", "battery", "trash", "shoes", "clothes"}
EXPECTED_CLASSES = RECYCLABLE_CLASSES | NON_RECYCLABLE_CLASSES

DISPLAY_LABELS: Dict[str, str] = {
    "metal": "Metal",
    "glass": "Glass",
    "paper": "Paper",
    "cardboard": "Cardboard",
    "plastic": "Plastic",
    "biological": "Biological",
    "battery": "Battery",
    "trash": "Trash",
    "shoes": "Shoes",
    "clothes": "Clothes",
}


def normalize_class(label: str | None) -> str:
    if label is None:
        return "unknown"
    value = str(label).strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "cardboard": "cardboard",
        "paper": "paper",
        "plastic": "plastic",
        "metal": "metal",
        "glass": "glass",
        "biological": "biological",
        "organic": "biological",
        "battery": "battery",
        "batteries": "battery",
        "trash": "trash",
        "garbage": "trash",
        "shoes": "shoes",
        "shoe": "shoes",
        "clothes": "clothes",
        "clothing": "clothes",
    }
    return aliases.get(value, value)


def display_class(label: str | None) -> str:
    normalized = normalize_class(label)
    return DISPLAY_LABELS.get(normalized, str(label or "Unknown").strip().title())


def is_recyclable(label: str | None) -> bool:
    return normalize_class(label) in RECYCLABLE_CLASSES


def expected_display_classes() -> List[str]:
    return [DISPLAY_LABELS[c] for c in sorted(EXPECTED_CLASSES)]
