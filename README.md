# Calificador Moodle + Grade Uploader UNED — Paquete portable

Kit completo y autocontenido para **calificar tareas de Moodle con ayuda de Claude Code** y luego **subir las notas oficiales al sistema de Captura de Notas Parciales de la UNED**. Sirve para **cualquier curso**: solo hay que cambiar el nombre del curso, la lista de estudiantes y los IDs de la tarea.

Esta carpeta se puede copiar o mover completa a cualquier computadora o workspace. No depende de nada externo, salvo Python 3.10+ y las credenciales que usted configure.

> **Aviso:** este es un proyecto comunitario no oficial; no está afiliado con
> Moodle, UNED ni Anthropic. Quien lo use debe respetar las políticas
> institucionales, verificar toda calificación y aprobar manualmente cualquier
> escritura en sistemas oficiales.

---

## Tabla de contenidos

1. [Qué contiene el paquete](#1-qué-contiene-el-paquete)
2. [Preparación inicial (una sola vez)](#2-preparación-inicial-una-sola-vez)
3. [Cómo usar el calificador de Moodle](#3-cómo-usar-el-calificador-de-moodle)
4. [Cómo usar el Grade Uploader (Captura de Notas UNED)](#4-cómo-usar-el-grade-uploader-captura-de-notas-uned)
5. [Checklist para cada curso nuevo](#5-checklist-para-cada-curso-nuevo)
6. [Seguridad](#6-seguridad)
7. [Desarrollo y licencia](#7-desarrollo-y-licencia)

---

## 1. Qué contiene el paquete

```
moodle-grader-portable/
├── README.md                     ← Esta guía
├── prompt.txt                    ← Prompt de calificación (editar por curso)
├── Users.example.md              ← Plantilla de la lista de estudiantes
├── requirements.txt              ← Dependencias Python
├── requirements-dev.txt          ← Pruebas y lint para contribuir
├── pyproject.toml                 ← Python 3.10+ y configuración de calidad
├── .env.example                  ← Plantilla de credenciales (copiar a .env)
├── .gitignore                    ← Protege .env, submissions/ y logs
├── LICENSE / NOTICE              ← Apache License 2.0 y atribución
├── SECURITY.md                   ← Reporte privado de vulnerabilidades
├── CONTRIBUTING.md               ← Reglas para contribuciones sin datos reales
│
├── CLAUDE.md                     ← Reglas esenciales siempre activas para Claude Code
├── .claude/
│   ├── settings.json             ← (opcional, lo crea usted) Permisos del proyecto, ver 2.4
│   ├── agents/
│   │   └── moodle-grader.md      ← Subagente que califica UNA entrega (corre en paralelo)
│   └── skills/moodle-grading/
│       ├── SKILL.md              ← Flujo de calificación en 8 pasos (/moodle-grading)
│       ├── grading-rules.md      ← Reglas INMUTABLES de calificación
│       ├── reference.md          ← Referencia CLI de los scripts y formatos de archivo
│       ├── log-instructions.md   ← Cómo descargar los logs de Moodle
│       └── scripts/
│           ├── check_env.py              ← Verifica credenciales sin mostrar secretos
│           ├── moodle_download.py        ← Descarga las entregas de los estudiantes
│           ├── extract_users.py          ← Genera Users.md desde logs de Moodle
│           ├── extract_submission_zip.py ← Extrae ZIPs de las entregas (seguro)
│           ├── build_summary.py          ← Valida notas contra la rúbrica y genera el resumen
│           ├── moodle_upload_grades.py   ← Sube nota + feedback a Moodle (opcional)
│           └── notasparciales_upload.py  ← Copia del uploader (ver grade-uploader/)
│
└── grade-uploader/               ← Herramienta independiente para Captura de Notas UNED
    ├── README.md                 ← Documentación completa y detallada del uploader
    ├── notasparciales_upload.py  ← El script principal
    ├── instalar.bat / instalar.ps1  ← Instalador automático (venv + dependencias)
    ├── construir_exe.bat         ← Genera un .exe portable (no requiere Python)
    ├── .env.example              ← Plantilla de credenciales del uploader
    └── requirements*.txt
```

**Las dos herramientas, en una frase cada una:**

| Herramienta | Qué hace |
|-------------|----------|
| **Calificador Moodle** | Claude Code descarga las entregas (PDF, imágenes, ZIP), las califica contra la rúbrica oficial y genera nota + retroalimentación por estudiante, más un resumen global. |
| **Grade Uploader** | Lee las notas finales (xlsx exportado de Moodle) y las sube en lote al sistema oficial de [Captura de Notas Parciales](https://produccion.uned.ac.cr/notasparciales/Formularios/CapturaNotas.aspx) de la UNED. |

---

## 2. Preparación inicial (una sola vez)

### 2.1 Abrir la carpeta en Claude Code

Copie esta carpeta a donde quiera, abra una terminal **en esa carpeta** (la raíz del workspace) y ejecute `claude`. Esto es importante: los scripts y el skill usan rutas relativas a la raíz, y `CLAUDE.md`, el skill y el subagente de `.claude/` solo se cargan si esta carpeta es la raíz.

### 2.2 Instalar dependencias

Requiere **Python 3.10 o superior**. En una terminal dentro de la carpeta:

```bash
python -m pip install -r requirements.txt
```

### 2.3 Configurar credenciales de Moodle

Copie la plantilla y complétela:

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

```bash
# Linux o macOS
cp .env.example .env
```

Abra `.env` con cualquier editor y complete al menos:

```ini
MOODLE_URL=https://aprende.uned.ac.cr    # URL base de su Moodle
MOODLE_USERNAME=su_usuario
MOODLE_PASSWORD=su_contraseña
```

> Si la contraseña tiene caracteres especiales, escríbala entre comillas dobles.
> El archivo `.env` **nunca** se comparte ni se sube a Git (el `.gitignore` ya lo protege).

> Claude Code no necesita leer su `.env`: el skill comprueba las credenciales con `check_env.py`, que solo informa qué variables están definidas, sin mostrar valores.

Las credenciales del **Grade Uploader** son aparte y se configuran en `grade-uploader/.env` (ver [sección 4.1](#41-configurar-credenciales-del-uploader)). La plantilla de la raíz también trae la sección `NP_*` por si prefiere correr el uploader desde la raíz del workspace (`.claude/skills/moodle-grading/scripts/notasparciales_upload.py` lee el `.env` de la raíz); si usa `grade-uploader/` como carpeta independiente, puede ignorar esa sección aquí.

### 2.4 (Opcional) Permisos del proyecto

Para evitar confirmaciones repetitivas en los scripts locales y proteger los secretos, puede crear `.claude/settings.json` con:

```json
{
  "permissions": {
    "allow": [
      "Bash(python .claude/skills/moodle-grading/scripts/check_env.py*)",
      "Bash(python .claude/skills/moodle-grading/scripts/extract_users.py*)",
      "Bash(python .claude/skills/moodle-grading/scripts/extract_submission_zip.py*)",
      "Bash(python .claude/skills/moodle-grading/scripts/build_summary.py*)"
    ],
    "ask": [
      "Bash(python .claude/skills/moodle-grading/scripts/moodle_upload_grades.py*)",
      "Bash(python .claude/skills/moodle-grading/scripts/notasparciales_upload.py*)",
      "Bash(python grade-uploader/notasparciales_upload.py*)"
    ],
    "deny": ["Read(./.env)", "Read(./grade-uploader/.env)"]
  }
}
```

Los scripts que escriben en sistemas oficiales (subida a Moodle y a Notas Parciales) siguen pidiendo confirmación en cada ejecución.

---

## 3. Cómo usar el calificador de Moodle

El calificador funciona conversando con **Claude Code**: usted da la instrucción (o escribe `/moodle-grading`) y el agente sigue el flujo definido en `SKILL.md`, pidiéndole confirmación en los puntos clave. Cada entrega la califica un subagente independiente (`moodle-grader`), en tandas paralelas, y un script (`build_summary.py`) verifica mecánicamente que ninguna nota se salga de la escala de la rúbrica. Estos son los pasos y lo que usted debe hacer en cada uno.

### 3.1 Configurar el prompt de calificación (por curso)

Abra [prompt.txt](prompt.txt) y:

1. Reemplace `#COURSE NAME PLACEHOLDER#` por el nombre real del curso (ej. «Curso de ejemplo (00000)»). Si no lo hace, el agente tomará el nombre del curso de las instrucciones de la tarea (sin modificar `prompt.txt`).
2. Si su curso lo requiere, ajuste las secciones obligatorias de ejemplo (portada, índice, introducción, etc.) y los tipos de ejercicio que se verifican matemáticamente.

**Qué NO se puede cambiar:** las reglas de [.claude/skills/moodle-grading/grading-rules.md](.claude/skills/moodle-grading/grading-rules.md) (resumidas en [CLAUDE.md](CLAUDE.md)) se aplican siempre y son innegociables: solo puntajes que existan en la escala de la rúbrica (nada de valores intermedios inventados), calificación en español, un solo párrafo de retroalimentación sin el nombre del estudiante, revisión del PDF completo, revisión de imágenes adjuntas y ZIPs antes de concluir que falta evidencia, y resumen final con casos límite para revisión del profesor.

### 3.2 Colocar el PDF de instrucciones de la tarea

Guarde el PDF con la consigna oficial de la tarea dentro del workspace (por ejemplo en una carpeta `tarea/`). El agente le pedirá **confirmar explícitamente** cuál archivo es la consigna antes de usarlo como fuente de la rúbrica — así se evita calificar con el enunciado equivocado.

### 3.3 Obtener los IDs de Moodle

Se necesitan dos números, ambos visibles en la URL del navegador:

| ID | Dónde verlo |
|----|-------------|
| **Course ID** | Entrando al curso: `.../course/view.php?id=8067` → el ID es `8067` |
| **Assignment cmid** | Entrando a la tarea: `.../mod/assign/view.php?id=517559` → el cmid es `517559` |

### 3.4 Preparar la lista de estudiantes (`Users.md`)

Dos opciones:

- **A mano:** cree `Users.md` en la raíz siguiendo el formato de [Users.example.md](Users.example.md) (tabla con User ID y nombre completo).
- **Automático desde logs:** descargue los logs del curso desde Moodle como CSV — guía ilustrada con capturas de pantalla en [.claude/skills/moodle-grading/log-instructions.md](.claude/skills/moodle-grading/log-instructions.md) (Informes → Registros → Conseguir estos registros → Descargar como .csv → guardar en el workspace) — y pídale al agente que genere `Users.md`, o córralo usted:

```bash
python .claude/skills/moodle-grading/scripts/extract_users.py "Logs Usuarios.csv" -o Users.md
```

### 3.5 Iniciar la calificación

Escriba el comando del skill con el curso y la tarea:

> `/moodle-grading 8067 517559`

o simplemente: «Quiero calificar la tarea con cmid 517559 del curso 8067».

El agente seguirá el flujo del skill:

1. Verifica credenciales y IDs.
2. Verifica o genera `Users.md`.
3. Descarga las entregas a `submissions/assignments/assignment_<cmid>/user_<id>/` (PDF, imágenes y ZIPs; los ZIP se extraen a `_extracted/`).
4. Le pide confirmar el PDF de la consigna.
5. **Le presenta la rúbrica resumida** (todos los rubros con sus valores permitidos) y **espera su aprobación** antes de calificar. Si la consigna no trae rúbrica, le propondrá una para que la apruebe. La rúbrica aprobada se guarda en `rubric.json`.
6. Califica cada entrega (un subagente por estudiante, hasta 5 en paralelo), escribe `grade_<userid>.txt` en la carpeta del estudiante y lo valida contra `rubric.json`.
7. Genera el resumen global (`build_summary.py`).

### 3.6 Validar los resultados

Al terminar, revise estos archivos (todos bajo `submissions/assignments/assignment_<cmid>/`):

| Archivo | Qué revisar |
|---------|-------------|
| `user_<id>/grade_<userid>.txt` | Nota por rubro, nota total y párrafo de retroalimentación de cada estudiante. |
| `grading_summary.csv` | Tabla maestra: una fila por estudiante con nota y estado (`calificado`, `sin_entrega`, `omitido_sin_pdf`, etc.). |
| `grading_resumen_global.md` | Informe legible con la tabla completa **y la sección «Casos que pueden requerir revisión del profesor»**. |
| `rubric.json` / `consigna.md` | La rúbrica y la consigna tal como fueron aprobadas; son la referencia con la que se validó cada nota. |

**Recomendación de validación mínima:** lea la sección de casos límite del resumen global y compare esas entregas contra el PDF real del estudiante; haga además un muestreo de 2-3 notas al azar. La calificación asistida es un borrador — **la decisión final siempre es del profesor**. Si no está de acuerdo con una nota, edite el `grade_<userid>.txt` (o pídale al agente que recalifique esa entrega) antes de subir nada.

### 3.7 (Opcional) Subir notas y retroalimentación a Moodle

Una vez validadas las notas, puede volcarlas al calificador de Moodle (nota + párrafo de feedback en el formulario de cada estudiante):

```bash
# Probar primero con un estudiante; dry-run es el valor predeterminado:
python .claude/skills/moodle-grading/scripts/moodle_upload_grades.py --assignment <CMID> --user <USERID>

# Si se ve bien, --commit habilita la escritura:
python .claude/skills/moodle-grading/scripts/moodle_upload_grades.py --assignment <CMID> --user <USERID> --commit

# Comprobar el lote completo y repetir con --commit solo tras revisarlo:
python .claude/skills/moodle-grading/scripts/moodle_upload_grades.py --assignment <CMID> --users-file Users.md
```

> Claude Code nunca debe usar `--commit` sin su autorización explícita en esa
> ejecución. Un puntaje que no coincide exactamente con un nivel de Moodle falla de forma
> segura. `--allow-approximate` permite el nivel más cercano únicamente como
> excepción explícita; revíselo antes de combinarlo con `--commit`.

La referencia completa de todos los scripts (parámetros, formatos, solución de problemas) está en [.claude/skills/moodle-grading/reference.md](.claude/skills/moodle-grading/reference.md).

---

## 4. Cómo usar el Grade Uploader (Captura de Notas UNED)

Cuando ya tenga las notas finales en Moodle, esta herramienta las sube en lote al sistema oficial de Notas Parciales, en lugar de digitarlas una por una. Trabaja desde `grade-uploader/` y tiene su propia documentación exhaustiva en [grade-uploader/README.md](grade-uploader/README.md); aquí va el flujo completo resumido.

### 4.1 Configurar credenciales del uploader

Dentro de `grade-uploader/`, ejecute `instalar.bat` (crea el venv, instala dependencias y copia `.env.example` a `.env`), o hágalo a mano. Luego edite `grade-uploader/.env` con **dos capas** de autenticación, ambas obligatorias:

**Capa 1 — NTLM (usuario del SSO UNED):**

```ini
NP_NTLM_USER=jperez              # SIN @uned.ac.cr
NP_NTLM_PASSWORD=su_contraseña   # la misma del Entorno de Funcionarios
```

**Capa 2 — Cookies de sesión (desde el navegador):**

1. Inicie sesión en https://produccion.uned.ac.cr/notasparciales/Formularios/CapturaNotas.aspx y verifique que carguen los dropdowns.
2. Presione `F12` → pestaña **Application** (Chrome/Edge) o **Almacenamiento** (Firefox) → Cookies → `https://produccion.uned.ac.cr`.
3. Copie los valores de las 3 cookies al `.env`:

```ini
NP_COOKIE_ASPNET_SESSIONID=...   # cookie ASP.NET_SessionId
NP_COOKIE_UZMX=...               # cookie uzmx
NP_COOKIE_UZMXJ=...              # cookie uzmxj
```

> Las cookies **expiran a los ~20 minutos de inactividad**. Si el script empieza a fallar, recargue la página (F5) y copie las 3 cookies de nuevo. Guía detallada por navegador con capturas: [grade-uploader/README.md](grade-uploader/README.md), sección «Cómo obtener las cookies».

### 4.2 Exportar el xlsx desde Moodle

En el curso: **Calificaciones → Exportar → Hoja de cálculo Excel**, seleccione las actividades y descargue. El archivo debe traer estas columnas (Moodle las genera solo si están configuradas):

- `Número de ID` → **debe ser la cédula** del estudiante (así se mapea contra Notas Parciales).
- `Institución` → el centro universitario con su código, ej. `SAN JOSE (01)`.
- Columnas de nota que terminen en `(Real)` o `(Porcentaje)` — el script las detecta solo y convierte de escala 0–100 a 0–10 automáticamente. Un guion `-` se interpreta como «no presentó».

### 4.3 Identificar los parámetros del curso

Cada comando necesita los valores que usted ve en los dropdowns de la página de Captura de Notas — anótelos una vez por curso:

| Parámetro | Dropdown en la página | Ejemplo |
|-----------|----------------------|---------|
| `--ano` | Año | `2026` |
| `--pac` | PAC (cuatrimestre) | `3` |
| `--tipo` | Tipo de matrícula | `O` (ordinaria, es el default) |
| `--escuela` | Escuela | `03` |
| `--catedra` | Cátedra | `253` |
| `--encargado` | Encargado de cátedra | `DOCENTE_EJEMPLO` |
| `--tutor` | Tutor (identificador ficticio) | `0000000001` |
| `--asignatura` | Asignatura (sigla ficticia) | `00000` |
| `--cu` | Centro universitario | `42` |
| `--grupo` | Grupo | `1` |
| `--modelo` | Modelo de evaluación | `4` |

### 4.4 Paso 1 — `probe`: verificar conexión

```bash
cd grade-uploader
python notasparciales_upload.py probe --ano 2026 --pac 3 --tipo O --escuela 03 --catedra 253 --encargado DOCENTE_EJEMPLO --tutor 0000000001 --asignatura 00000 --cu 42 --grupo 1 --modelo 4
```

Si todo está bien, muestra «cookies válidas», la nota mínima de aprobación, los **códigos de instrumento** del modelo (`Tar1`, `Tar2`, `Proy1`…) y cuántos estudiantes hay en el grupo. **Siempre empiece por aquí.**

### 4.5 Paso 2 — `plan`: generar y validar el plan

```bash
python notasparciales_upload.py plan --ano 2026 --pac 3 --tipo O --escuela 03 --catedra 253 --encargado DOCENTE_EJEMPLO --tutor 0000000001 --asignatura 00000 --modelo 4 --xlsx calificaciones_moodle.xlsx --cu-grupo 42=1 --cu-grupo 01=2 --output notas_plan.csv
```

- `--cu-grupo 42=1` mapea el centro universitario 42 al grupo 1 del sistema (repetible por cada CU del curso).
- Si una columna del xlsx no se mapea sola a un instrumento, fuerce el mapeo: `--map 'Tarea 1 (Real)=Tar1'`.

**Validar el plan (importante):** abra `notas_plan.csv` en Excel y revise fila por fila las columnas `accion` y `motivo`. Las acciones que escriben son `upload` y `mark_not_presented`; `would_overwrite` solo se ejecuta con `--allow-update`; `review` requiere decisión manual. No siga adelante si algo no tiene sentido.

### 4.6 Paso 3 — `apply`: dry-run y luego commit

```bash
# Primero SIEMPRE en dry-run (no escribe nada):
python notasparciales_upload.py apply --ano 2026 --pac 3 --tipo O --escuela 03 --catedra 253 --encargado DOCENTE_EJEMPLO --tutor 0000000001 --asignatura 00000 --modelo 4 --plan notas_plan.csv --dry-run

# Cuando esté seguro, ejecutar de verdad:
python notasparciales_upload.py apply --ano 2026 --pac 3 --tipo O --escuela 03 --catedra 253 --encargado DOCENTE_EJEMPLO --tutor 0000000001 --asignatura 00000 --modelo 4 --plan notas_plan.csv --commit
```

**Validar el resultado:** al terminar se genera `notas_plan_resultados.csv` con el estado de cada operación — revíselo, y además verifique 2-3 notas directamente en la página de Captura de Notas para confirmar que quedaron bien.

### 4.7 Problemas frecuentes

| Síntoma | Solución |
|---------|----------|
| «respuesta no-JSON» / «Probable expiración de cookies» | Las cookies expiraron: recargue la página (F5) y copie las 3 cookies nuevas al `.env`. |
| `HTTP 401` | Credenciales NTLM mal: verifique `NP_NTLM_USER` (sin `@uned.ac.cr`) y la contraseña. |
| «Cédula no aparece en el roster oficial del grupo» | El `Número de ID` en Moodle no coincide con la cédula en Notas Parciales: corríjalo en Moodle y re-exporte. |

La tabla completa de solución de problemas (10+ casos), los modos `single` y `csv`, y cómo generar un `.exe` portable están en [grade-uploader/README.md](grade-uploader/README.md).

---

## 5. Checklist para cada curso nuevo

Lo único que cambia de un curso (o cuatrimestre) a otro:

- [ ] Editar `prompt.txt`: nombre del curso y, si aplica, secciones obligatorias.
- [ ] Crear el `Users.md` del curso (a mano o desde logs con `extract_users.py`).
- [ ] Anotar el Course ID y el Assignment cmid de cada tarea (de las URLs de Moodle).
- [ ] Colocar el PDF de instrucciones de cada tarea en el workspace.
- [ ] Para el uploader: anotar los parámetros del curso (`--ano`, `--pac`, `--catedra`, `--asignatura`, `--modelo`, mapeo `--cu-grupo`, etc.).
- [ ] Verificar que en Moodle el campo «Número de ID» de los estudiantes tenga la cédula.

**Lo que nunca cambia:** los scripts, el skill, las reglas de calificación, y sus credenciales en `.env` (salvo las cookies del uploader, que se refrescan en cada sesión).

---

## 6. Seguridad

- **`.env` (raíz y `grade-uploader/`) contiene contraseñas y cookies de sesión.** Nunca lo suba a Git, ni lo comparta por correo o chat. Los `.gitignore` incluidos ya lo excluyen — verifique con `git status` antes de cualquier push.
- **`submissions/`, `grades/` y los logs `logs_*.csv` contienen datos de estudiantes** (nombres, trabajos, notas). También están excluidos por `.gitignore`; trátelos con la misma confidencialidad que las actas de notas.
- Si sospecha que sus credenciales se filtraron, **cambie inmediatamente su contraseña del SSO UNED**.
- Las cookies del uploader expiran solas (~20 min), pero cerrar la sesión del navegador las invalida antes.

Consulte [SECURITY.md](SECURITY.md) para reportar vulnerabilidades sin publicar
datos sensibles. Las contribuciones deben cumplir [CONTRIBUTING.md](CONTRIBUTING.md).

## 7. Desarrollo y licencia

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest
```

El código se distribuye bajo [Apache License 2.0](LICENSE). Consulte
[NOTICE](NOTICE) para la atribución y el descargo de afiliación.
