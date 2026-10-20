# Modelo de datos: Asistente de consulta del AI Act

## Fuente normativa

Representa el HTML oficial local utilizado para construir el índice.

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `source_id` | texto | Identificador estable; combina CELEX y hash del contenido. |
| `celex_id` | texto | Para esta entrega, `32024R1689`. |
| `source_url` | URL | URL oficial de EUR-Lex. |
| `language` | código | `es`. |
| `source_hash` | texto | SHA-256 del archivo original. |
| `retrieved_at` | fecha-hora UTC | Momento en que se guardó el origen, si se conoce. |
| `document_title` | texto | Título oficial detectado o fijado en configuración. |

Un cambio en el hash representa una nueva fuente y requiere regenerar el índice y repetir la
 evaluación.

## Fragmento normativo

Unidad exacta extraída del texto para recuperación y evidencia visible.

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `chunk_id` | texto | Único e idempotente por fuente, unidad estructural, apartado e índice de fragmento. |
| `source_id` | texto | Referencia a la fuente normativa. |
| `unit_type` | enumeración | `considerando`, `articulo` o `anexo`. |
| `unit_number` | texto | Número visible; admite números romanos para anexos. |
| `unit_title` | texto opcional | Encabezado textual de la unidad, cuando exista. |
| `paragraph_number` | texto opcional | Apartado de artículo largo; no inventar uno si la fuente no lo marca. |
| `chunk_index` | entero | Orden de fragmento dentro de la misma unidad y apartado. |
| `canonical_reference` | texto | Formato: `[Artículo 6]`, `[Considerando 12]` o `[Anexo III]`; apartado opcional si es necesario. |
| `text` | texto | Pasaje exacto, no paráfrasis. |
| `content_hash` | texto | Permite comprobar idempotencia y cambios de fragmentación. |

La referencia canónica se extrae de la estructura original. `chunk_id` y `canonical_reference`
tienen propósitos distintos: varios fragmentos pueden compartir la misma referencia jurídica. Los
fragmentos se presentan como evidencia, nunca como instrucciones para el modelo.

## Consulta

Solicitud transitoria de la persona usuaria. No se persiste como historial y su texto no se registra.

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `question` | texto | Obligatorio, español, no vacío tras quitar espacios, máximo 1.000 caracteres. |
| `k` | entero opcional | Por defecto 5; debe ser positivo y no exceder el máximo de configuración. |

## Respuesta

Resultado de una consulta, devuelto sin crear historial.

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `answer` | texto | Español; respuesta breve o frase de abstención. |
| `references` | lista de texto | Referencias citadas; todas corresponden a fragmentos recuperados. |
| `evidence` | lista de fragmento | Fragmentos exactos usados, incluyendo texto y referencia. |
| `disclaimer` | texto | Aviso informativo de que no constituye asesoramiento jurídico. |
| `abstained` | booleano | Verdadero cuando no hay evidencia suficiente. |

La respuesta sustantiva no se entrega si la validación detecta una cita inexistente o no respaldada;
el error registrado no contiene pregunta ni respuesta completa.

## Caso de evaluación

Pregunta versionada para comprobar recuperación, validez de citas y abstención.

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `case_id` | texto | Identificador único y estable en el dataset. |
| `question` | texto | Pregunta española; evitar datos personales. |
| `expected_references` | lista de referencia | Al menos una para caso respondible; vacía para no respondible. |
| `unanswerable` | booleano | Verdadero si el Reglamento no contiene respuesta a la pregunta. |
| `notes` | texto opcional | Justificación breve de la referencia o condición no respondible. |

Invariantes: al menos 12 casos en el conjunto y 3 con `unanswerable=true`. Los casos no
respondibles se excluyen del denominador de `recall@5`.

## Ejecución de evaluación

Registro de ejecución reproducible del sistema sobre una versión del dataset.

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `run_id` | texto | Identificador único, sin secretos. |
| `timestamp_utc` | fecha-hora | Fecha de ejecución UTC. |
| `dataset_version` | texto | Versión o hash del dataset evaluado. |
| `configuration` | objeto | Embedding, `k`, modelo generativo y parámetros no secretos. |
| `recall_at_5` | porcentaje | Referencias esperadas halladas en los cinco primeros fragmentos / referencias esperadas totales en casos respondibles. |
| `valid_citation_rate` | porcentaje | Respuestas sustantivas con todas las citas válidas / respuestas sustantivas evaluadas. |
| `correct_refusal_rate` | porcentaje | Casos no respondibles correctamente rechazados / casos no respondibles. |

Si un denominador es cero, el informe devuelve `null` y lo explica; no lo presenta como 0 %.
