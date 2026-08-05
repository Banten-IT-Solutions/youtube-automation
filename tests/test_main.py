import sys

sys.path.insert(0, ".")

from main import _is_unprocessed_draft_title


def test_unprocessed_draft_title():
    assert _is_unprocessed_draft_title("ABUYA UCI CILONGOK")
    assert _is_unprocessed_draft_title(" | ABUYA UCI CILONGOK")
    assert not _is_unprocessed_draft_title("189 PENGAJIAN KITAB IBANATUL AHKAM - ABUYA UCI CILONGOK")
