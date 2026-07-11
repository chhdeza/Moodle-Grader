---
name: moodle-grading
description: End-to-end workflow for downloading and grading Moodle student assignment submissions. Revisa PDF, imágenes adjuntas y contenido extraído de archivos ZIP; retroalimentación en español sin mencionar el nombre del estudiante en el párrafo de feedback. Calificación estricta a la escala de la rúbrica (sin puntajes inventados). Genera resumen final con notas de todos los estudiantes y sección de casos límite para revisión del profesor. Use when the user wants to grade homework, download assignments, extract student lists from Moodle logs, or evaluate PDF submissions using a rubric.
---

# Moodle Assignment Grading Workflow

Guides the user through a complete grading cycle: verify credentials, build a student list, download submissions, and grade each submission bundle (PDF + attachments + optional ZIP contents) against the assignment rubric.

**Language:** All grading output, feedback paragraphs, rubric tables, and summaries MUST be written in **Spanish**. The courses are taught in Spanish at UNED Costa Rica.

**Immutable grading rules** are enforced by the Cursor Rule at `.cursor/rules/grading-prompt.mdc` (alwaysApply). Before grading any file, always read `prompt.txt` for the full evaluation criteria.

**Rúbrica — escala estricta:** Cada puntaje por ítem y la nota total deben derivarse **solo** de valores que la rúbrica/consigna autoriza explícitamente. No usar medias, decimales ni enteros «intermedios» que no estén en la escala declarada. La nota total = suma de los puntajes de la tabla (ver regla 3 en `grading-prompt.mdc`).

**Scripts** are bundled inside this skill at `.cursor/skills/moodle-grading/scripts/`. Run them from the workspace root.

## Workflow

Copy this checklist and track progress:

```
Progreso de calificación:
- [ ] Paso 1: Verificar credenciales e ID del curso
- [ ] Paso 2: Obtener o generar la lista de estudiantes
- [ ] Paso 3: Descargar entregas
- [ ] Paso 4: Confirmar cuál es el PDF de instrucciones de la tarea y obtenerlo
- [ ] Paso 5: Presentar resumen de rúbrica al usuario
- [ ] Paso 6: Calificar todas las entregas
- [ ] Paso 7: Generar resumen de calificaciones
```

---

### Paso 1: Verificar credenciales e ID del curso

Ask the user for:
- **Course ID** (numeric, from the Moodle URL `course/view.php?id=XXXX`)
- **Assignment cmid** (from `mod/assign/view.php?id=XXXX`)

Then verify `.env` exists in the workspace root with `MOODLE_URL`, `MOODLE_USERNAME`, and `MOODLE_PASSWORD`. Check by reading the file (never print the password).

If `.env` is missing or incomplete:
1. Tell the user exactly which values are needed.
2. Point them to `.env.example` as a template.
3. **Stop here.** Do not proceed without valid credentials.

Optional validation — run from the workspace root:

```bash
python .cursor/skills/moodle-grading/scripts/moodle_download.py --in-progress --course <ID>
```

If it fails, report the error and stop.

---

### Paso 2: Obtener o generar la lista de estudiantes

Ask the user: *"¿Tiene un archivo `Users.md` con la lista de estudiantes, o necesita generarlo a partir de archivos de log de Moodle?"*

**If the user has `Users.md`:** verify it follows the expected format (see [reference.md](reference.md)). Proceed to Paso 3.

**If the user needs to generate it:**
1. Ask them to provide one or more Moodle log CSV files. For instructions on downloading logs, see [log-instructions.md](log-instructions.md).
2. **Stop and wait.** The workflow cannot continue without log files or a Users.md.
3. When the user provides CSV files, run:

```bash
python .cursor/skills/moodle-grading/scripts/extract_users.py <log1.csv> <log2.csv> -o Users.md
```

4. Show the user how many students were extracted and confirm before proceeding.

---

### Paso 3: Descargar entregas

Inform the user that the download script will now fetch files for each student. Run:

```bash
python .cursor/skills/moodle-grading/scripts/moodle_download.py --course <COURSE_ID> --assignment <ASSIGNMENT_CMID> --users-file Users.md
```

Add `--group <ID>` if the user specified a group filter.

**Output location:** each student’s files are saved under `<download-dir>/assignments/assignment_<ASSIGNMENT_CMID>/user_<USERID>/` (default `--download-dir` is `submissions`). Each assignment cmid has its own directory; each student has a `user_<id>` subfolder.

**Monitor output for:**
- Students marked as "skipped (no attached files)" — these get a `no_submission_found.txt` placeholder.
- Any connection or download errors.

**Report results to the user:** how many downloaded, how many skipped, any errors.

The download script waits **1 second** between each student (rate limit); see [reference.md](reference.md).

If the process fails mid-way, it can be re-run. Existing folders will be overwritten.

---

### Paso 4: Confirmar y obtener el PDF de instrucciones de la tarea

**Obligatorio — confirmación explícita:** Antes de usar cualquier documento como consigna oficial, el asistente **debe** obtener del usuario la identificación inequívoca del archivo (ruta en el workspace y/o nombre del archivo) y **pedir confirmación explícita** de que ese PDF es el de las instrucciones de **esta** tarea (no otro PDF del curso, no una versión antigua, no el enunciado de otra actividad).

1. Preguntar qué archivo es el PDF de instrucciones: *ruta completa relativa al workspace* o *nombre exacto del archivo*, según lo que el usuario tenga a mano.
2. **Repetir en el chat** la identificación propuesta, por ejemplo: *«¿Confirma que el PDF de la consigna es `ruta/al/archivo.pdf`?»* (o el nombre si no hay ambigüedad). Si hay varios PDFs candidatos en la carpeta, listarlos y pedir que indiquen cuál es el correcto **antes** de confirmar.
3. **Detenerse y esperar** una confirmación afirmativa del usuario. Sin esa confirmación, **no** continuar a Paso 5 ni leer el PDF como fuente de rúbrica.
4. Tras la confirmación, leer el PDF **completo** (todas las páginas).

Si el usuario aún no ha colocado el archivo en el workspace, indicar dónde conviene guardarlo y repetir el paso de confirmación cuando esté disponible.

---

### Paso 5: Presentar resumen de rúbrica al usuario

After reading the assignment instructions:

1. **Replace** `#COURSE NAME PLACEHOLDER#` in `prompt.txt` with the actual course name (from the assignment file or from Paso 1).
2. Present to the user **in Spanish**:
   - A summary of the assignment requirements (what students must deliver).
   - The grading rubric as a table with **every** item, its **maximum** for that item, and the **conjunto exacto de valores permitidos** por ítem (p. ej. «solo 0, 3 o 6» o «enteros de 0 a 5»). Si la consigna solo da un máximo sin niveles, indicar explícitamente que en calificación se usarán **solo enteros de 0 al máximo** de ese ítem, sin otros valores.
3. **If no rubric is found** in the assignment file, ask the user to provide one. If the user cannot provide one, propose a rubric based on the assignment requirements and ask for approval — la propuesta debe **definir valores permitidos** por ítem (o regla clara, p. ej. enteros 0–N) para que Paso 6 no pueda inventar puntajes.
4. **Wait for user confirmation** before proceeding to grading.
5. **Recordatorio al usuario:** a partir de aquí, **toda** calificación debe limitarse a esos valores; cualquier desviación invalida la entrega del proceso de calificación asistida.

---

### Paso 6: Calificar todas las entregas

**CRITICAL: Before grading, read `prompt.txt` to load the immutable grading instructions. These instructions are also enforced by the Cursor Rule `.cursor/rules/grading-prompt.mdc`. ALL grading output MUST be in Spanish.**

Treat each `user_<userid>/` folder under `<download-dir>/assignments/assignment_<ASSIGNMENT_CMID>/` as a **single submission bundle**. Each assignment (cmid) has its own directory under `assignments/`; students are separated by `user_<id>/`. Do **not** skip a folder merely because it contains non-PDF files alongside the PDF.

**Files to ignore** when deciding what to grade (metadata / output): `no_submission_found.txt` (only if it is the sole placeholder for no submission), `grade_*.txt`, and editor junk (e.g. `.DS_Store`).
**Note:** If `_extracted/` already exists from a prior run, you may skip re-running the extract script unless the ZIP files changed.

For each student folder `user_<USERID>/` under `<download-dir>/assignments/assignment_<ASSIGNMENT_CMID>/` for **this** assignment:

1. **List all student folders** sorted alphabetically by the student name from `Users.md`.
2. **Resume:** if `grade_<userid>.txt` already exists, skip (already graded).
3. If the folder contains a `no_submission_found.txt` placeholder and **no** PDF → skip, estado `sin_entrega`.
4. If there is **no** `.pdf` file in the folder (ignoring `grade_*.txt`) → skip, estado `omitido_sin_pdf` (do not grade image-only or ZIP-only submissions unless the assignment instructions explicitly allow it; default is **≥1 PDF** required).
5. **ZIP files:** if any `.zip` exists in the folder, run **before** evaluating rubric items that require evidence inside the archive:

```bash
python .cursor/skills/moodle-grading/scripts/extract_submission_zip.py submissions/assignments/assignment_<ASSIGNMENT>/user_<USERID>
```

   - Extraction goes to `_extracted/<nombre_sanitizado>/` under that folder. See [reference.md](reference.md).
   - If extraction fails (corrupto, contraseña, demasiado grande), **state this in the retroalimentación** (impersonal Spanish) and score rubric items accordingly — do not assume silence means missing work.
6. **Evidence outside the PDF:** inventory **images** in the folder (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`) and **PDFs/images/code** under `_extracted/`. When the consigna or rubric requires **capturas**, **evidencia de cuestionario**, **código fuente**, etc., **check these files** before concluding that evidence is missing. If the PDF does not show a capture but an image in the same folder satisfies the requirement, **do not** penalize for “missing in PDF”; cite generically (e.g. “en la imagen adjunta” o “en el material extraído del archivo ZIP”).
7. **Grade** the main PDF fully (all pages), using the union of evidence from the folder + extracted contents for rubric criteria.

   **Cumplimiento estricto de la escala (obligatorio antes de escribir la tabla):**
   - Para cada fila de la rúbrica, asignar **solo** un valor del conjunto permitido acordado en Paso 5 / `prompt.txt` (nunca 2,5 si la escala es 0/3/6; nunca «7» si el máximo del ítem es 5).
   - **Recalcular la nota total** como suma de esos puntajes y comprobar que coincide con la línea `Nota total: X / Y` (donde `Y` es la suma de máximos por rubro según la rúbrica).
   - Si dos niveles de la escala encajan mal, elegir **uno** de los valores permitidos y, si aplica, marcar al estudiante en Paso 7 como caso límite por ambigüedad de nivel — **no** inventar un puntaje intermedio.

8. **Write** `grade_<userid>.txt` in the same folder, **in Spanish**:
   - **Identificación:** nombre del estudiante (solo aquí).
   - Tabla de evaluación con puntajes.
   - Nota total.
   - **Retroalimentación:** un solo párrafo — **sin nombre del estudiante** (ni tratamiento con nombre), solo voz impersonal o tercera persona (“el trabajo”, “el documento”, “se observa…”).

---

### Paso 7: Generar resumen de calificaciones

When all students have been processed, generate **two** artifacts under `<download-dir>/assignments/assignment_<ASSIGNMENT_CMID>/` (same directory that contains the `user_*` folders):

**1. `grading_summary.csv`** — **una fila por cada estudiante** del proceso (incluidos sin entrega u omitidos), con todas las notas y estados. Debe ser la tabla maestra importable (similar al formato de exportación de Moodle con columnas de tarea y retroalimentación si el usuario lo pide después). La columna de nota debe reflejar **solo** sumas coherentes con la escala de la rúbrica (mismos límites que en cada `grade_<userid>.txt`).

```csv
User ID,Nombre Estudiante,Nota,Nota Máxima,Estado
655,ANA EJEMPLO SOLANO,0,101,sin_entrega
3081,JUAN EJEMPLO MORA,84,101,calificado
3547,LUIS EJEMPLO CASTRO,0,101,omitido_sin_pdf
```

**2. `grading_resumen_global.md`** — informe en español para el profesor con:

- **Tabla resumen de todos los estudiantes:** misma información que el CSV en formato legible (markdown), orden recomendado: por apellido o por `User ID`, de forma **consistente** en todo el documento.
- **Sección obligatoria: «Casos que pueden requerir revisión del profesor»** — lista **destacada** (viñetas o tabla) solo de entregas donde la calificación automática o asistida pueda ser **menos fiable** o donde convenga **confirmación humana** según la consigna y el contenido visto. Incluir **User ID** y nombre para localizar la carpeta `assignments/assignment_<ASSIGNMENT_CMID>/user_<USERID>/`.

**Criterios orientativos para marcar un caso (usar juicio; no es lista cerrada):**

- Nota **en zona límite** respecto al criterio de aprobación o a un umbral explícito en la rúbrica (p. ej. muy cerca del mínimo), si la consigna lo hace relevante.
- **Ambigüedad** entre lo exigido en la consigna y lo entregado (p. ej. evidencia en adjunto o ZIP interpretable de más de una forma).
- **PDF escaneado** o baja legibilidad que dificulta verificar conversiones o secciones con la misma seguridad que un PDF con texto.
- **ZIP** corrupto, incompleto, cifrado o parcialmente revisado; o conflicto entre contenido del PDF y archivos extraídos.
- **Rúbrica** con ítems que dependen de criterio subjetivo fuerte y la puntuación asignada es **discutible** frente al documento.
- Cualquier situación en la que, al comparar **instrucciones + contenido del estudiante**, tengas **dudas razonables** sobre la nota o sobre un rubro concreto.

Para cada caso marcado, indicar **en una o dos frases** el **motivo** de la advertencia (en español) y, si aplica, qué convendría revisar (sin sustituir el criterio final del profesor).

**En la respuesta al usuario (chat):** mostrar la **tabla completa de notas** de todos los estudiantes y, a continuación, la **sección de casos límite** resaltada; más los totales agregados:

- Total de estudiantes procesados
- Calificados (con promedio y nota máxima de referencia)
- Omitidos: sin entrega / sin PDF / otros
- Errores (archivos corruptos, ilegibles, ZIP inválido)
- **Número de casos marcados para revisión** y recordatorio de que la decisión final es del profesor

---

### Paso 8 (opcional): Subir calificaciones a Moodle

Una vez generados todos los archivos `grade_<userid>.txt`, se pueden volcar las calificaciones directamente al servidor Moodle.

**Script:** `moodle_upload_grades.py`

Requiere solo `MOODLE_USERNAME` y `MOODLE_PASSWORD` en `.env` (sin token). Autentica mediante sesión de navegador, descarga el formulario HTML de calificación de cada estudiante, mapea los puntajes de la rúbrica local a los `levelid` internos de Moodle, y envía el formulario con la nota y el párrafo de retroalimentación.

```bash
# Un solo estudiante (dry-run es el comportamiento predeterminado):
python .cursor/skills/moodle-grading/scripts/moodle_upload_grades.py \
    --assignment <CMID> --user <USERID>

# Solo --commit permite enviar de verdad:
python .cursor/skills/moodle-grading/scripts/moodle_upload_grades.py \
    --assignment <CMID> --user <USERID> --commit

# Batch de comprobación (todos los estudiantes; no escribe):
python .cursor/skills/moodle-grading/scripts/moodle_upload_grades.py \
    --assignment <CMID> --users-file Users.md
```

**Notas importantes:**
- El mapeo de criterios es **posicional** (ítem 1 del .txt → criterio 1 de la rúbrica en Moodle). El orden debe coincidir.
- Si un puntaje del `.txt` no existe exactamente como nivel de la rúbrica de Moodle, ese estudiante falla de forma segura y no se envía. `--allow-approximate` habilita el nivel más cercano únicamente como excepción explícita y debe revisarse antes de combinarlo con `--commit`.
- El campo de **retroalimentación** (cuadro de comentarios del profesor) se rellena con el párrafo del .txt.
- La directorio de entregas por defecto es `submissions/` con estructura `assignments/assignment_<CMID>/user_<UID>/`. Cambiar con `--submissions-dir`.

## Additional resources

- CLI reference and file formats: [reference.md](reference.md)
- How to download Moodle logs: [log-instructions.md](log-instructions.md)
