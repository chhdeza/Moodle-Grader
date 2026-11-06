from __future__ import annotations

from conftest import load_script

check_env = load_script(
    "check_env",
    ".claude/skills/moodle-grading/scripts/check_env.py",
)


def test_missing_file_reports_all_required(tmp_path):
    missing, problems = check_env.check_env(tmp_path / ".env")
    assert missing == list(check_env.REQUIRED)
    assert problems


def test_complete_env_passes_and_never_prints_secrets(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text(
        "MOODLE_URL=https://moodle.example.org\nMOODLE_USERNAME=profe\nMOODLE_PASSWORD=s3cret-value\n",
        encoding="utf-8",
    )

    assert check_env.main(["--env", str(env)]) == 0
    out = capsys.readouterr()
    assert "s3cret-value" not in out.out + out.err
    assert "profe" not in out.out + out.err


def test_incomplete_or_malformed_env_fails(tmp_path):
    env = tmp_path / ".env"
    env.write_text("MOODLE_URL=moodle.example.org\nMOODLE_USERNAME=profe\n", encoding="utf-8")

    missing, problems = check_env.check_env(env)

    assert missing == ["MOODLE_PASSWORD"]
    assert problems
    assert check_env.main(["--env", str(env)]) == 1
