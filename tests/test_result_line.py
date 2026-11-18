import pytest
from src.formatting import result_line


@pytest.fixture(autouse=True)
def fixed_terminal_width(monkeypatch):
    # result_line wraps to the terminal width. Pin it so tests don't depend on the machine.
    monkeypatch.setenv("COLUMNS", "80")


def test_result_line_short():
    paper = {"title": "Title", "id": "12.1234"}
    assert result_line(3, paper, 1) == "3. Title (12.1234)"
def test_result_line_short_padding():
    # Tests when the prefix (100) is longer than the number width (1)
    paper = {"title": "Title", "id": "12.1234"}
    assert result_line(100, paper, 1) == "100. Title (12.1234)"
def test_result_line_extra_padding():
    paper = {"title": "Title", "id": "12.1234"}
    assert result_line(3, paper, 10) == (" " * 9) + "3. Title (12.1234)"


PAPER = {"title": "Title", "id": "12.1234"}
LONG_TITLE = " ".join(f"word{i}" for i in range(60))


def test_result_line_default_width_is_two():
    assert result_line(3, PAPER) == " 3. Title (12.1234)"


def test_result_line_zero_width_adds_no_padding():
    assert result_line(3, PAPER, 0) == "3. Title (12.1234)"


def test_result_line_titles_line_up_with_the_same_width():
    paper = {"title": "Alpha", "id": "1.1"}
    columns = {result_line(n, paper, 3).index("Alpha") for n in (1, 9, 10, 99, 100)}
    assert len(columns) == 1


def test_result_line_negative_number_does_not_crash():
    assert result_line(-5, PAPER, 3) == " -5. Title (12.1234)"


def test_result_line_rejects_non_integer_width():
    with pytest.raises((TypeError, ValueError)):
        result_line(3, PAPER, 2.0)


def test_result_line_missing_field_raises_key_error():
    with pytest.raises(KeyError):
        result_line(1, {"title": "Title"}, 1)


def test_result_line_newline_in_title_becomes_a_space():
    # The arXiv API often returns titles with line breaks in them.
    line = result_line(1, {"title": "First half\nsecond half", "id": "1.1"}, 1)
    assert line == "1. First half second half (1.1)"


def test_result_line_long_title_wraps_within_terminal_width(monkeypatch):
    monkeypatch.setenv("COLUMNS", "60")
    lines = result_line(1, {"title": LONG_TITLE, "id": "1.1"}, 3).split("\n")
    assert len(lines) > 1
    assert all(len(line) <= 60 for line in lines)


def test_result_line_wrapped_lines_are_indented_under_the_title(monkeypatch):
    monkeypatch.setenv("COLUMNS", "60")
    width = 4
    lines = result_line(1, {"title": LONG_TITLE, "id": "1.1"}, width).split("\n")
    indent = width + 2   # padded number, ".", space
    for line in lines[1:]:
        assert line.startswith(" " * indent)
        assert not line[indent].isspace()


def test_result_line_wrapped_title_still_lines_up_between_numbers(monkeypatch):
    monkeypatch.setenv("COLUMNS", "50")
    paper = {"title": LONG_TITLE, "id": "1.1"}
    one = result_line(1, paper, 3).split("\n")
    big = result_line(100, paper, 3).split("\n")
    assert one[1:] == big[1:]
    assert one[0].index("word0") == big[0].index("word0")


def test_result_line_padding_wider_than_terminal_does_not_crash_or_lose_text(monkeypatch):
    monkeypatch.setenv("COLUMNS", "40")
    line = result_line(3, PAPER, 200)
    assert line.split() == ["3.", "Title", "(12.1234)"]
