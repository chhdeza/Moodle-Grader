from __future__ import annotations

import csv

from conftest import load_script

extract_users = load_script(
    "extract_users",
    ".claude/skills/moodle-grading/scripts/extract_users.py",
)


def test_collect_users_warns_on_conflicting_names(tmp_path, capsys):
    log_file = tmp_path / "moodle_log.csv"
    with log_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["Nombre completo del usuario", "Descripción"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "Nombre completo del usuario": "ESTUDIANTE EJEMPLO UNO",
                "Descripción": "The user with id '1001' viewed the course.",
            }
        )
        writer.writerow(
            {
                "Nombre completo del usuario": "ESTUDIANTE EJEMPLO DOS",
                "Descripción": "The user with id '1001' viewed the course.",
            }
        )

    users = extract_users.collect_users([str(log_file)])

    assert users == {"1001": "ESTUDIANTE EJEMPLO UNO"}
    assert "conflicting names" in capsys.readouterr().err
