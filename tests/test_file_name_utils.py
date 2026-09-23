from src.utils.file_name_utils import accepted_files, find_item_file, list_available_items, natural_key


def make_files(folder, names):
    for name in names:
        (folder / name).write_bytes(b"x")


def test_natural_key_orders_numbers_numerically():
    assert sorted(["10.tif", "2.tif", "1.tif"], key=natural_key) == ["1.tif", "2.tif", "10.tif"]


def test_accepted_files_filters_extension_and_ignores_case(tmp_path):
    make_files(tmp_path, ["A.TIF", "b.tiff", "c.png", "d.txt"])
    names = [p.name for p in accepted_files(tmp_path, [".tif", ".tiff"])]
    assert names == ["A.TIF", "b.tiff"]


def test_accepted_files_missing_folder_returns_empty(tmp_path):
    assert accepted_files(tmp_path / "nao_existe", None) == []


def test_find_item_file_by_regex_label(tmp_path):
    make_files(tmp_path, ["10 FRENTE.tif", "2.tif"])
    category = {"folder_path": str(tmp_path), "item_label_regex": r"^(\d+)", "extensions": [".tif"]}
    assert find_item_file(category, "10").name == "10 FRENTE.tif"
    assert find_item_file(category, "99") is None


def test_list_available_items_sorted_naturally(tmp_path):
    make_files(tmp_path, ["10.tif", "2.tif", "1.tif"])
    category = {"folder_path": str(tmp_path), "item_label_regex": r"^(\d+)"}
    assert list_available_items(category) == ["1", "2", "10"]
