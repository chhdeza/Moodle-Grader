from __future__ import annotations

from conftest import load_script

download = load_script(
    "moodle_download",
    ".claude/skills/moodle-grading/scripts/moodle_download.py",
)


class FakeResponse:
    headers = {}

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size):
        yield b"content"


class FakeSession:
    def get(self, url, timeout, stream):
        return FakeResponse()


def test_duplicate_filenames_are_not_overwritten(tmp_path):
    files = [
        ("https://example.invalid/first", "evidence.pdf"),
        ("https://example.invalid/second", "evidence.pdf"),
    ]

    saved = download.download_submission_files(FakeSession(), files, str(tmp_path))

    assert [path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1] for path in saved] == [
        "evidence.pdf",
        "evidence_2.pdf",
    ]
    assert len(list(tmp_path.iterdir())) == 2
