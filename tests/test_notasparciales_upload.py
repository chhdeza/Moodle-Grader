from __future__ import annotations

from pathlib import Path

import pytest
from conftest import ROOT, load_script

uploader = load_script(
    "notasparciales_upload",
    "grade-uploader/notasparciales_upload.py",
)


def test_retirado_detection_uses_dynamic_instruments():
    row = {
        "Cedula": "0000000002",
        "Nombre": "ESTUDIANTE EJEMPLO",
        "Tar4": uploader.NOTA_RETIRADO,
        "Exam1": uploader.NOTA_RETIRADO,
    }

    assert uploader._is_retirado(row)
    assert uploader._is_retirado(row, ["Tar4", "Exam1"])

    row["Exam1"] = uploader.NOTA_NO_NOTA
    assert not uploader._is_retirado(row)


def test_legacy_body_identifiers_reject_quotes():
    with pytest.raises(ValueError, match="caracteres no permitidos"):
        uploader._validate_literal_identifier("encargado", "DOCENTE'ALTERADO")


def test_uploader_copies_remain_identical():
    standalone = Path(ROOT, "grade-uploader/notasparciales_upload.py").read_bytes()
    skill_copy = Path(
        ROOT,
        ".cursor/skills/moodle-grading/scripts/notasparciales_upload.py",
    ).read_bytes()

    assert standalone == skill_copy
