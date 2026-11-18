from src.formatting import result_line

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