# Política de seguridad

## Versiones compatibles

Solo la versión más reciente de la rama principal recibe correcciones de
seguridad.

## Reportar una vulnerabilidad

No publique credenciales, cookies, cédulas, entregas ni calificaciones en un
issue. Use la opción **Report a vulnerability** de GitHub (Security Advisories)
si está habilitada. Si no lo está, contacte de forma privada a la persona
propietaria del repositorio.

Incluya una descripción reproducible con datos ficticios. Se confirmará la
recepción y se coordinará la divulgación después de preparar una corrección.

## Si se expuso información sensible

1. Retire el material del área pública sin volver a copiarlo en otro commit.
2. Cambie inmediatamente la contraseña afectada.
3. Cierre las sesiones activas para invalidar cookies.
4. Rote tokens de Moodle y cualquier otra credencial expuesta.
5. Reescriba el historial de Git si el secreto llegó a un commit y avise a las
   personas que clonaron el repositorio.

Los archivos `.env`, `Users.md`, logs, entregas, exportaciones XLSX, planes CSV
y HTML de depuración son privados y están excluidos por `.gitignore`.
