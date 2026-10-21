# Guía rápida de validación: Asistente de consulta del AI Act

Esta guía describe comprobaciones de extremo a extremo que se ejecutarán una vez implementado el
proyecto.

## Requisitos previos

- Python 3.11 o superior y uv.
- Clave Anthropic válida para responder consultas reales; las pruebas automatizadas no la usan.
- HTML oficial español del Reglamento (UE) 2024/1689 guardado en `data/raw/`.
- Acceso inicial a la red para descargar el modelo local de embeddings; la recuperación no usa un
  servicio de embeddings remoto.

## Configuración local

1. Sincronizar el entorno desde `pyproject.toml` y `uv.lock` con uv.
2. Copiar `.env.example` a `.env` y definir `ANTHROPIC_API_KEY` y el identificador del modelo
   soportado. No añadir `.env` a Git.
3. Confirmar que `data/raw/` contiene el HTML oficial español. El proceso no debe descargar o
   sustituir silenciosamente el origen.

## Pruebas automatizadas

Ejecutar pytest. Se espera que todas las pruebas pasen y que ninguna contacte Anthropic ni servicios
pagados. Las pruebas de API usan el cliente de pruebas de FastAPI; la generación se simula.

Validaciones mínimas:

- Ingesta: un fixture HTML con considerando, artículo corto, artículo subdividido y anexo produce
  referencias y fragmentos esperados; HTML incompleto falla explícitamente.
- Recuperación: `k=5` por defecto; `k` configurado limita resultados sin exceder los disponibles;
  metadatos conservados.
- Generación: contexto delimitado, respuesta en español y frase fija de abstención sin evidencia.
- Citas: se aceptan solo referencias existentes en fragmentos proporcionados; una cita ajena se
  rechaza sin filtrar el texto generado en el error.
- API: pregunta vacía, solo con espacios, mayor de 1.000 caracteres o en otro idioma rechazada;
  `/health` refleja disponibilidad del
  índice; `/ask` retorna respuesta, referencias, evidencia y aviso legal.
- Privacidad: logs de solicitudes y errores no contienen preguntas, respuestas completas, claves
  ni cabeceras de autorización.

## Ingesta e índice

Colocar o actualizar el HTML oficial en `data/raw/`, ejecutar la ingesta con el límite por defecto
de 1.500 caracteres y verificar que el índice persistente se crea en `chroma_db/`. La subdivisión
respeta apartados/definiciones, letras, puntos, secciones y párrafos antes de recurrir a frases;
cada subfragmento mantiene la referencia jurídica y su localizador. La segunda ejecución con
fuente y configuración iguales debe ser idempotente, sin duplicar fragmentos. Revisar cantidades
por tipo y longitudes, y contrastar una muestra con el origen.

## Servicio y escenarios de aceptación

Iniciar FastAPI localmente y validar `GET /health`, `POST /ask` y la página HTML:

1. Pregunta respondible: respuesta clara con cita exacta, fragmento y aviso legal.
2. Pregunta fuera del Reglamento: abstención sin afirmación jurídica ni cita inventada.
3. Pregunta ambigua: pedir aclaración cuando no se determine la disposición aplicable.
4. Entrada vacía, mayor de 1.000 caracteres o idioma no admitido: rechazo sin generación normativa.
5. Intento de ignorar instrucciones: mantener la limitación a evidencia del Reglamento.

## Evaluación reproducible

Verificar que `data/eval/questions.jsonl` contiene al menos 12 casos respondibles/no respondibles,
con referencias esperadas en los respondibles y al menos 3 no respondibles. Ejecutar el evaluador y
comprobar que escribe en `evals/results/` un informe con fecha UTC, versión/hash del dataset,
configuración no secreta, `recall@5`, tasa de citas válidas y tasa de rechazo correcto. `recall@5`
usa las referencias esperadas presentes en los cinco primeros fragmentos recuperados. Comparar
informes solo si el dataset y su versión están identificados en ambos.

## Contratos y modelo

Las formas y errores HTTP se describen en [contracts/openapi.yaml](contracts/openapi.yaml); los
campos, restricciones y relaciones se detallan en [data-model.md](data-model.md).
