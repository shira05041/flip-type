"""Convert text typed with the wrong keyboard layout (English <-> Hebrew SI-1452)."""

# Key-by-key mapping: what you get on the Hebrew layout when pressing the English key.
EN_TO_HE = {
    "q": "/", "w": "'", "e": "ק", "r": "ר", "t": "א", "y": "ט", "u": "ו",
    "i": "ן", "o": "ם", "p": "פ",
    "a": "ש", "s": "ד", "d": "ג", "f": "כ", "g": "ע", "h": "י", "j": "ח",
    "k": "ל", "l": "ך", ";": "ף", "'": ",",
    "z": "ז", "x": "ס", "c": "ב", "v": "ה", "b": "נ", "n": "מ", "m": "צ",
    ",": "ת", ".": "ץ", "/": ".",
}

HE_TO_EN = {he: en for en, he in EN_TO_HE.items()}


def _has_hebrew(text: str) -> bool:
    return any("א" <= ch <= "ת" for ch in text)


def detect_target(text: str) -> str:
    """Return the language the text should be converted to: 'en' or 'he'."""
    return "en" if _has_hebrew(text) else "he"


def convert(text: str) -> tuple[str, str]:
    """Convert text to the other layout.

    Returns (converted_text, target_language) where target_language is 'he' or 'en'.
    Characters without a mapping (spaces, digits, newlines...) are left unchanged.
    """
    target = detect_target(text)
    if target == "en":
        out = "".join(HE_TO_EN.get(ch, ch) for ch in text)
    else:
        out = "".join(EN_TO_HE.get(ch.lower(), ch) for ch in text)
    return out, target
