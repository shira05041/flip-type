import pytest

from fliptype.converter import EN_TO_HE, HE_TO_EN, convert


@pytest.mark.parametrize(
    "typed, expected, target",
    [
        ("akuo", "שלום", "he"),
        ("akuo kfo", "שלום לכם", "he"),
        ("AKUO", "שלום", "he"),
        ("tbh ,ux", "אני תוס", "he"),
        ("ah,v.", "שיתהץ", "he"),
        ("יקךךם", "hello", "en"),
        ("שלום", "akuo", "en"),
        ("יקךךם 'םרךג", "hello world", "en"),
        ("123 akuo\nkfo", "123 שלום\nלכם", "he"),
    ],
)
def test_convert(typed, expected, target):
    assert convert(typed) == (expected, target)


def test_mapping_is_reversible():
    assert len(HE_TO_EN) == len(EN_TO_HE)
    for en, he in EN_TO_HE.items():
        assert HE_TO_EN[he] == en


def test_round_trip():
    text = "hello world"
    he, _ = convert(text)
    back, target = convert(he)
    assert back == text and target == "en"


def test_empty():
    assert convert("") == ("", "he")
