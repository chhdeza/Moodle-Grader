from __future__ import annotations

import csv
import json

import pytest
from conftest import load_script

build_summary = load_script(
    "build_summary",
    ".claude/skills/moodle-grading/scripts/build_summary.py",
)

RUBRIC = {
    "curso": "CURSO DE EJEMPLO",
    "nota_aprobacion": 7,
    "items": [
        {"rubro": "Portada", "max": 3, "valores": [0, 3]},
        {"rubro": "Ejercicios", "max": 5},
    ],
}

GOOD_GRADE = """Estudiante: ANA EJEMPLO SOLANO

| Rubro | Puntaje |
|-------|---------|
| Portada | 3 / 3 |
| Ejercicios | 4 / 5 |

Nota total: 7 / 8

Retroalimentación:
El trabajo presenta una estructura completa y ejercicios mayormente correctos.
"""


@pytest.fixture
def rubric(tmp_path):
    path = tmp_path / "rubric.json"
    path.write_text(json.dumps(RUBRIC), encoding="utf-8")
    return build_summary.load_rubric(path)


def write_grade(tmp_path, text, uid=1001):
    folder = tmp_path / f"user_{uid}"
    folder.mkdir(exist_ok=True)
    path = folder / f"grade_{uid}.txt"
    path.write_text(text, encoding="utf-8")
    return path


def test_valid_grade_passes(tmp_path, rubric):
    _, errors, warnings = build_summary.validate_grade_file(write_grade(tmp_path, GOOD_GRADE), rubric)
    assert errors == []
    assert warnings == []


def test_score_outside_allowed_values_is_rejected(tmp_path, rubric):
    text = GOOD_GRADE.replace("| Portada | 3 / 3 |", "| Portada | 2 / 3 |").replace(
        "7 / 8", "6 / 8"
    )
    _, errors, _ = build_summary.validate_grade_file(write_grade(tmp_path, text), rubric)
    assert any("no permitido" in e for e in errors)


def test_total_must_equal_sum_of_table(tmp_path, rubric):
    text = GOOD_GRADE.replace("Nota total: 7 / 8", "Nota total: 8 / 8")
    _, errors, _ = build_summary.validate_grade_file(write_grade(tmp_path, text), rubric)
    assert any("suma de la tabla" in e for e in errors)


def test_declared_maximum_must_match_rubric(tmp_path, rubric):
    text = GOOD_GRADE.replace("7 / 8", "7 / 10")
    _, errors, _ = build_summary.validate_grade_file(write_grade(tmp_path, text), rubric)
    assert any("suma de máximos" in e for e in errors)


def test_rubric_item_order_and_count_are_checked(tmp_path, rubric):
    text = GOOD_GRADE.replace("| Ejercicios | 4 / 5 |\n", "")
    _, errors, _ = build_summary.validate_grade_file(write_grade(tmp_path, text), rubric)
    assert any("rubros" in e for e in errors)


def test_student_name_in_feedback_is_rejected(tmp_path, rubric):
    text = GOOD_GRADE.replace("El trabajo presenta", "Ana Solano presenta")
    _, errors, _ = build_summary.validate_grade_file(write_grade(tmp_path, text), rubric)
    assert any("nombre del estudiante" in e for e in errors)


def test_feedback_must_be_single_paragraph(tmp_path, rubric):
    text = GOOD_GRADE + "\nUn segundo párrafo no permitido.\n"
    _, errors, _ = build_summary.validate_grade_file(write_grade(tmp_path, text), rubric)
    assert any("un solo párrafo" in e for e in errors)


def test_default_values_are_integers_up_to_max(rubric):
    assert rubric["items"][1]["valores"] == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    assert rubric["max_total"] == 8


def test_invalid_rubric_is_rejected(tmp_path):
    path = tmp_path / "rubric.json"
    path.write_text(json.dumps({"items": [{"rubro": "Solo nombre"}]}), encoding="utf-8")
    with pytest.raises(ValueError):
        build_summary.load_rubric(path)


def test_pre_status_triage(tmp_path):
    graded = tmp_path / "user_1"
    graded.mkdir()
    (graded / "grade_1.txt").write_text("x", encoding="utf-8")
    pending = tmp_path / "user_2"
    pending.mkdir()
    (pending / "tarea.PDF").write_bytes(b"%PDF")
    nothing = tmp_path / "user_3"
    nothing.mkdir()
    (nothing / "no_submission_found.txt").write_text("", encoding="utf-8")
    zip_only = tmp_path / "user_4"
    zip_only.mkdir()
    (zip_only / "entrega.zip").write_bytes(b"PK")

    assert build_summary.pre_status(graded, 1) == "calificado"
    assert build_summary.pre_status(pending, 2) == "pendiente"
    assert build_summary.pre_status(nothing, 3) == "sin_entrega"
    assert build_summary.pre_status(zip_only, 4) == "omitido_sin_pdf"
    assert build_summary.pre_status(tmp_path / "user_9", 9) == "pendiente_sin_carpeta"


def test_build_writes_csv_and_markdown_with_review_section(tmp_path, capsys):
    rubric_path = tmp_path / "rubric.json"
    rubric_path.write_text(json.dumps(RUBRIC), encoding="utf-8")
    users = tmp_path / "Users.md"
    users.write_text(
        "| User ID | Nombre completo |\n|---|---|\n"
        "| 1001 | ANA EJEMPLO SOLANO |\n| 1002 | JUAN EJEMPLO MORA |\n",
        encoding="utf-8",
    )
    write_grade(tmp_path, GOOD_GRADE, uid=1001)
    nothing = tmp_path / "user_1002"
    nothing.mkdir()
    (nothing / "no_submission_found.txt").write_text("", encoding="utf-8")
    (tmp_path / "review_flags.json").write_text(
        json.dumps({"1001": {"revisar": "Evidencia ambigua en el ZIP."}}), encoding="utf-8"
    )

    code = build_summary.main(
        ["--assignment-dir", str(tmp_path), "--users-file", str(users)]
    )

    assert code == 0
    with (tmp_path / "grading_summary.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == ["User ID", "Nombre Estudiante", "Nota", "Nota Máxima", "Estado"]
    assert rows[1] == ["1001", "ANA EJEMPLO SOLANO", "7", "8", "calificado"]
    assert rows[2] == ["1002", "JUAN EJEMPLO MORA", "0", "8", "sin_entrega"]
    report = (tmp_path / "grading_resumen_global.md").read_text(encoding="utf-8")
    assert "Casos que pueden requerir revisión del profesor" in report
    assert "Evidencia ambigua en el ZIP." in report
    assert "zona límite" in report  # 7 is within the 5% band of nota_aprobacion=7


def test_build_fails_when_a_pdf_submission_is_ungraded(tmp_path):
    rubric_path = tmp_path / "rubric.json"
    rubric_path.write_text(json.dumps(RUBRIC), encoding="utf-8")
    folder = tmp_path / "user_5"
    folder.mkdir()
    (folder / "tarea.pdf").write_bytes(b"%PDF")

    assert build_summary.main(["--assignment-dir", str(tmp_path), "--users-file", ""]) == 1


def test_error_messages_survive_a_cp1252_console(tmp_path):
    """Regression: '≠' in an error message crashed scripts on Windows consoles (cp1252)."""
    import os
    import subprocess
    import sys

    rubric_path = tmp_path / "rubric.json"
    rubric_path.write_text(json.dumps(RUBRIC), encoding="utf-8")
    grade = write_grade(tmp_path, GOOD_GRADE.replace("| Portada |", "| Cubierta |"))
    env = {**os.environ, "PYTHONIOENCODING": "cp1252"}

    result = subprocess.run(
        [
            sys.executable,
            str(build_summary.__file__),
            "--rubric",
            str(rubric_path),
            "--validate",
            str(grade),
        ],
        capture_output=True,
        env=env,
        check=False,
    )

    assert result.returncode == 1
    assert b"Traceback" not in result.stderr
    assert "≠".encode() in result.stdout
