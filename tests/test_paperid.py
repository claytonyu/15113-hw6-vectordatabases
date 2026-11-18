import pytest
from src.store import paper_id
def test_paper_id_removes_version():
    assert paper_id("123.445v35") == "123.445"
def test_paper_id_keeps_versionless():
    assert paper_id("36.24") == "36.24"
def test_paper_id_works_empty():
    assert paper_id("") == ""

## AI-Generated Tests
def test_paper_id_strips_version_from_new_style_id():
    assert paper_id("2401.01234v2") == "2401.01234"


# Old-style IDs (archive/NNNNNNN), used before April 2007
@pytest.mark.parametrize("given, expected", [
    ("hep-th/9901001v1", "hep-th/9901001"),
    ("math.GT/0309136v2", "math.GT/0309136"),   # archive with a subject class
])
def test_paper_id_handles_old_style_ids(given, expected):
    assert paper_id(given) == expected


def test_paper_id_keeps_a_v_with_no_digits():
    assert paper_id("2401.01234v") == "2401.01234v"


def test_paper_id_ignores_surrounding_whitespace():
    assert paper_id("\t 2401.01234v2\n") == "2401.01234"


def test_paper_id_blank_gives_empty_string():
    assert paper_id("   ") == ""


def test_paper_id_rejects_non_strings():
    with pytest.raises((TypeError, AttributeError)):
        paper_id(None)
