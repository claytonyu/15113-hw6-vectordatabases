from src.store import paper_id

def test_paper_id_removes_version():
    assert paper_id("123.445v35") == "123.445"

def test_paper_id_keeps_versionless():
    assert paper_id("36.24") == "36.24"

def test_paper_id_works_empty():
    assert paper_id("") == ""