from __future__ import annotations

import stat
import zipfile

from conftest import load_script

extractor = load_script(
    "extract_submission_zip",
    ".cursor/skills/moodle-grading/scripts/extract_submission_zip.py",
)


def test_extracts_regular_file(tmp_path):
    archive = tmp_path / "submission.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("evidence/readme.txt", "contenido")

    ok, _ = extractor.extract_zip(archive, tmp_path / "out", 1024)

    assert ok
    assert (tmp_path / "out/evidence/readme.txt").read_text() == "contenido"


def test_rejects_zip_slip(tmp_path):
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../outside.txt", "no")

    ok, message = extractor.extract_zip(archive, tmp_path / "out", 1024)

    assert not ok
    assert "path no seguro" in message
    assert not (tmp_path / "outside.txt").exists()


def test_rejects_symlink(tmp_path):
    archive = tmp_path / "symlink.zip"
    link = zipfile.ZipInfo("link")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(link, "target.txt")

    ok, message = extractor.extract_zip(archive, tmp_path / "out", 1024)

    assert not ok
    assert "enlace simbólico" in message


def test_rejects_size_and_entry_limits(tmp_path):
    archive = tmp_path / "large.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("one.txt", "12345")
        zf.writestr("two.txt", "67890")

    ok_size, _ = extractor.extract_zip(archive, tmp_path / "size", 5)
    ok_count, _ = extractor.extract_zip(archive, tmp_path / "count", 100, max_entries=1)

    assert not ok_size
    assert not ok_count
