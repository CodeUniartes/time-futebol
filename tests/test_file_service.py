from src.services.file_service import FileService


def test_make_order_folder_never_overwrites(tmp_path):
    service = FileService()
    info = {"numero_pedido": "1", "cliente": "Maria"}
    first = service.make_order_folder(tmp_path, info)
    second = service.make_order_folder(tmp_path, info)
    assert first != second and first.exists() and second.exists()


def test_copy_file_duplicate_mode_creates_one_copy_per_quantity(tmp_path):
    source = tmp_path / "1.tif"
    source.write_bytes(b"x")
    copied = FileService().copy_file(source, tmp_path / "out", 3, "duplicate_files")
    assert len(copied) == 3 and source.exists()


def test_copy_file_prefix_quantity_mode_creates_single_file(tmp_path):
    source = tmp_path / "1.tif"
    source.write_bytes(b"x")
    copied = FileService().copy_file(source, tmp_path / "out", 3, "prefix_quantity")
    assert len(copied) == 1 and "3x" in copied[0]
