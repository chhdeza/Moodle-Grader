# Contribuir

Gracias por mejorar Moodle-Grader. Mantenga los cambios simples, revisables y
compatibles con Python 3.10 o superior.

## Datos permitidos

- Use únicamente nombres, identificadores, calificaciones, URLs y archivos
  completamente ficticios.
- Nunca incluya entregas, cédulas, logs, cookies, tokens, contraseñas ni
  capturas de sistemas institucionales con datos reales.
- Anonimizar visualmente no basta si el archivo conserva metadatos sensibles.

## Flujo de desarrollo

1. Instale `requirements-dev.txt`.
2. Añada o actualice pruebas offline; ninguna prueba debe contactar Moodle,
   UNED u otro servicio externo.
3. Ejecute:

   ```bash
   python -m ruff check .
   python -m pytest
   ```

4. Verifique `git status` antes de publicar.
5. Use Conventional Commits, por ejemplo `fix: require explicit grade commit`.

Las reglas inmutables de calificación, la escala estricta de la rúbrica y el
objetivo del skill no deben debilitarse.
