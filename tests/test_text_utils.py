from src.utils.text_utils import parse_comma_items, safe_filename, slugify


def test_slugify_removes_accents_and_symbols():
    assert slugify("Atlético Mineiro") == "atletico_mineiro"


def test_slugify_fallback_when_empty():
    assert slugify("!!!") == "sem_nome"


def test_safe_filename_replaces_invalid_chars():
    assert not set(safe_filename(r'a<b>c:d"e/f\g|h?i*j')) & set(r'<>:"/\|?*')


def test_safe_filename_fallback():
    assert safe_filename("", "pedido") == "pedido"


def test_parse_comma_items_skips_blanks():
    assert parse_comma_items("A, B,, C ,") == ["A", "B", "C"]
