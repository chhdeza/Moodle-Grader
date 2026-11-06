from __future__ import annotations

import pytest
from conftest import load_script

upload = load_script(
    "moodle_upload_grades",
    ".claude/skills/moodle-grading/scripts/moodle_upload_grades.py",
)


def test_parse_documented_two_column_grade_file(tmp_path):
    grade_file = tmp_path / "grade_1001.txt"
    grade_file.write_text(
        """Estudiante: ESTUDIANTE EJEMPLO
User ID: 1001

| Rubro | Puntaje |
|---|---|
| Portada | 3 / 3 |
| Contenido | 6/6 |

Nota total: 9 / 9

Retroalimentación:
El trabajo cumple con los criterios.
""",
        encoding="utf-8",
    )

    parsed = upload.parse_grade_file(str(grade_file))

    assert parsed is not None
    assert parsed["student_name"] == "ESTUDIANTE EJEMPLO"
    assert parsed["userid"] == 1001
    assert parsed["rubric_items"] == [
        {"label": "Portada", "score": 3.0},
        {"label": "Contenido", "score": 6.0},
    ]
    assert parsed["total"] == 9.0


def test_parse_three_column_grade_file(tmp_path):
    grade_file = tmp_path / "grade_1002.txt"
    grade_file.write_text(
        """Nombre: ESTUDIANTE EJEMPLO

| # | Criterio | Puntaje |
|---|---|---|
| 1 | Exactitud | 10 |

Nota total: 10 / 10
Retroalimentación:
El documento es correcto.
""",
        encoding="utf-8",
    )

    parsed = upload.parse_grade_file(str(grade_file))

    assert parsed is not None
    assert parsed["rubric_items"] == [{"label": "Exactitud", "score": 10.0}]


def test_rubric_matching_requires_exact_score():
    items = [{"label": "Criterio", "score": 5.0}]
    rubric = [{"id": 10, "levels": [{"id": 20, "score": 3.0}, {"id": 21, "score": 6.0}]}]

    with pytest.raises(ValueError, match="no exact level"):
        upload.match_items_to_levels(items, rubric, verbose=False)

    assert upload.match_items_to_levels(
        items, rubric, verbose=False, allow_approximate=True
    ) == {10: 21}


def test_rubric_matching_rejects_item_count_mismatch():
    with pytest.raises(ValueError, match="has 0 items"):
        upload.match_items_to_levels([], [{"id": 1, "levels": []}], verbose=False)
