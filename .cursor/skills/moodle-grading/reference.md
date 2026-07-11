# Reference — Moodle Grading Skill

All scripts live at `.cursor/skills/moodle-grading/scripts/`. Run them from the workspace root.

## Scripts

### moodle_download.py

Downloads student submission files from Moodle assignments.

#### Environment variables (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `MOODLE_URL` | Yes | Base URL (e.g. `https://aprende.uned.ac.cr`) |
| `MOODLE_USERNAME` | Yes | Login username |
| `MOODLE_PASSWORD` | Yes | Login password. Wrap in double quotes if it contains special chars: `"'pass\"word"` |
| `MOODLE_TOKEN` | No | Web Services API token (enables REST API mode for single-user queries) |

#### Commands

```bash
# List in-progress courses
python .cursor/skills/moodle-grading/scripts/moodle_download.py --in-progress

# Show structure for a specific course
python .cursor/skills/moodle-grading/scripts/moodle_download.py --in-progress --course 8067

# Download submissions for all students
python .cursor/skills/moodle-grading/scripts/moodle_download.py --course 8067 --assignment 517559 --users-file Users.md

# Download for a single student
python .cursor/skills/moodle-grading/scripts/moodle_download.py --course 8067 --assignment 517559 --user 3081

# With group filter and custom output directory
python .cursor/skills/moodle-grading/scripts/moodle_download.py --course 8067 --assignment 517559 --users-file Users.md --group 38525 --download-dir hw2

# Debug mode
python .cursor/skills/moodle-grading/scripts/moodle_download.py --course 8067 --assignment 517559 --user 655 --debug
```

#### Output structure

(`<download-dir>` defaults to `submissions`.)

```
submissions/
└── assignments/
    └── assignment_517559/           ← Moodle assignment cmid; separate folder per assignment
        ├── user_655/
        │   └── no_submission_found.txt
        ├── user_3081/
        │   ├── Tarea2_EstudianteEjemplo.pdf
        │   ├── captura_cuestionario.png
        │   ├── evidencias.zip
        │   ├── _extracted/
        │   │   └── evidencias/
        │   │       └── extra.png
        │   └── grade_3081.txt       ← created during grading
        ├── grading_summary.csv      ← all students, one row each
        └── grading_resumen_global.md
```

#### Technical notes

- Uses `action=grade` (server-rendered), NOT `action=grader` (JS SPA).
- Filters `pluginfile.php` URLs: only `assignsubmission` paths, excludes `/intro/`.
- 1-second delay between users to avoid server overload.
- Files are saved under `<download-dir>/assignments/assignment_<cmid>/user_<userid>/`. The `--course` flag only scopes course listing / validation; it does not change this path.

---

### extract_users.py

Extracts distinct student user IDs from Moodle log CSV files.

```bash
# Basic usage (auto-detects course name from CSV)
python .cursor/skills/moodle-grading/scripts/extract_users.py log1.csv log2.csv

# With explicit course name and output file
python .cursor/skills/moodle-grading/scripts/extract_users.py *.csv --course-name "TELEMATICA Y REDES" -o Users.md
```

#### How it works

1. Reads the `Descripción` column for patterns like `The user with id '3081'`.
2. Pairs each user ID with the `Nombre completo del usuario` column.
3. Deduplicates by user ID, sorts numerically, writes markdown table.

---

### extract_submission_zip.py

Extrae archivos `.zip` en la carpeta de entrega de un estudiante hacia `_extracted/<nombre_sanitizado>/` con protección contra zip-slip, enlaces simbólicos y bombas ZIP. Los límites predeterminados son 200 MB descomprimidos y 10 000 entradas.

```bash
python .cursor/skills/moodle-grading/scripts/extract_submission_zip.py submissions/assignments/assignment_517559/user_3081

# Ajustar límite (MB)
python .cursor/skills/moodle-grading/scripts/extract_submission_zip.py path/to/folder --max-mb 200

# Ajustar también el máximo de entradas
python .cursor/skills/moodle-grading/scripts/extract_submission_zip.py path/to/folder --max-files 5000
```

- Si la carpeta `_extracted/<nombre>/` ya tiene contenido, ese ZIP se omite (no sobrescribe).
- **ZIP corrupto o con contraseña:** el script imprime el error; el evaluador debe reflejarlo en la retroalimentación (sin nombre del estudiante en el párrafo de feedback).

---

## File Formats

### Users.md

Markdown table with user IDs and names. Created by `extract_users.py` or manually.

```markdown
| User ID | Nombre completo |
|---------|-----------------|
| 655 | ANA EJEMPLO SOLANO |
| 3081 | JUAN EJEMPLO MORA |
```

Also accepts plain user IDs (one per line).

### Moodle log CSV files

Exported from Moodle: course → Informes → Registros → Descargar como CSV.

Required columns:
- `Nombre completo del usuario` — student full name
- `Descripción` — contains `The user with id 'NNNN'`
- `Contexto del evento` — contains `Curso: COURSE_NAME` (used for auto-detection)

### grading_summary.csv

Generated after grading completes. **One row per student** (everyone in the batch, including skipped or error states). Headers in Spanish. Use as the master table for grades before optional Moodle import.

```csv
User ID,Nombre Estudiante,Nota,Nota Máxima,Estado
655,ANA EJEMPLO SOLANO,0,101,sin_entrega
3081,JUAN EJEMPLO MORA,84,101,calificado
3547,LUIS EJEMPLO CASTRO,0,101,omitido_sin_pdf
7916,MARIA EJEMPLO ROJAS,0,101,error_pdf_corrupto
```

Status values: `calificado`, `sin_entrega`, `omitido_sin_pdf`, `error_pdf_corrupto`, `error_ilegible`.

### grading_resumen_global.md

Informe en español en `<download-dir>/assignments/assignment_<ASSIGNMENT_CMID>/grading_resumen_global.md` que incluye:

1. **Tabla o lista completa** de todos los estudiantes con nota y estado (equivalente legible al CSV).
2. **Sección «Casos que pueden requerir revisión del profesor»:** solo estudiantes donde la evaluación asistida puede ser menos fiable o conviene confirmación humana (notas límite, ambigüedad consigna–entrega, PDF escaneado difícil, problemas con ZIP/adjuntos, rubros muy subjetivos, etc.). Por cada uno: User ID, nombre, motivo breve. El profesor tiene la última palabra.

Este archivo complementa el CSV (retroalimentación agregada y alertas), similar en espíritu a exportaciones de calificaciones con columna de retroalimentación por estudiante (p. ej. exportación CSV del libro de calificaciones de Moodle).

### grade_<userid>.txt

One file per graded student, saved in `<download-dir>/assignments/assignment_<ASSIGNMENT_CMID>/user_<userid>/`. **Written entirely in Spanish.**

El **nombre del estudiante** aparece solo en la identificación inicial. El **párrafo de retroalimentación no debe incluir el nombre**.

```
Estudiante: JUAN EJEMPLO MORA

| Rubro | Puntaje |
|-------|---------|
| Portada | 3 / 3 |
| Índice | 3 / 3 |
| ... | ... |

Nota total: 84 / 101

Retroalimentación:
El trabajo presenta una estructura académica completa...
```

---

## Finding Moodle IDs

| ID | Where to find it |
|----|-----------------|
| Course ID | `course/view.php?id=8067` → `8067`, or run `--in-progress` |
| Assignment cmid | `mod/assign/view.php?id=517559` → `517559` |
| User ID | `&userid=3081` in grader URL, or from logs/Users.md |
| Group ID | `&group=38525` in filtered assignment URL |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| All users get the same file | Using `action=grader` (JS SPA) | Ensure `fetch_grader_page` uses `action=grade` |
| "No courses found" | Dynamic page loading | Script falls back to AJAX via `sesskey` automatically |
| `.env` parse error | Special chars in password | Wrap in double quotes: `MOODLE_PASSWORD="'pass"` |
| Wrong files downloaded | Intro PDF matched | `_is_submission_file_url` excludes `/intro/` paths |
| Script fails mid-batch | Network timeout | Re-run the same command; existing folders get overwritten |
| ZIP no extrae | Contraseña o corrupto | Revisar mensaje del script; reflejar en retroalimentación y rúbrica |
| Evidencia “no vista” | Solo se revisó el PDF | Revisar imágenes en la carpeta y `_extracted/` tras extraer ZIP |
