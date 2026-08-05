from core.steps.reuse import _latest_text, series_name


def test_series_name():
    assert series_name("189 IBANATUL AHKAM.mp4") == "IBANATUL AHKAM"
    assert series_name("188 IBANATUL AHKAM") == "IBANATUL AHKAM"
    assert series_name("TAFSIR JALALAIN.mp4") == "TAFSIR JALALAIN"
    assert series_name(None) == ""


def test_latest_text_picks_highest_number():
    texts = [
        "189 IBANATUL AHKAM",
        "188 IBANATUL AHKAM",
        "190 IBANATUL AHKAM",
    ]
    assert _latest_text(texts, "ibanatul ahkam") == "190 IBANATUL AHKAM"


def test_latest_text_prefers_numbered_over_unnumbered():
    texts = [
        "IBANATUL AHKAM (tanpa nomor)",
        "188 IBANATUL AHKAM",
    ]
    assert _latest_text(texts, "ibanatul ahkam") == "188 IBANATUL AHKAM"


def test_latest_text_no_match():
    assert _latest_text(["187 TAFSIR JALALAIN"], "ibanatul ahkam") is None
