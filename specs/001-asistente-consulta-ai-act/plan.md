# Plan de implementación: Asistente de consulta del AI Act

<!-- Plan en español; los identificadores y comentarios del código se escribirán en inglés. -->

**Rama**: sin rama (no se creó) | **Fecha**: 2026-10-20 | **Especificación**: [spec.md](spec.md)

**Entrada**: `specs/001-asistente-consulta-ai-act/spec.md`

## Resumen

Se construirá un asistente RAG de una sola fuente que responde en español sobre el texto oficial español del Reglamento (UE) 2024/1689. La ingesta convierte el HTML oficial local de `data/raw/` en fragmentos estructurales con referencias y metadatos, y persiste embeddings locales en Chroma. La API recupera cinco fragmentos por defecto, solicita una respuesta fundamentada al SDK oficial de Anthropic, valida cada cita frente a la evidencia recuperada y devuelve respuesta, referencias, fragmentos y aviso legal. Se incluyen una interfaz HTML mínima y una evaluación reproducible.

## Contexto técnico

**Lenguaje/versión**: Python 3.11 o superior; uv administra el proyecto y las dependencias.

**Dependencias principales**: FastAPI, Chroma, sentence-transformers, SDK oficial de Anthropic,
Beautiful Soup, python-dotenv y langdetect; pytest y HTTPX para pruebas.

**Almacenamiento**: HTML oficial en `data/raw/`; preguntas de evaluación en `data/eval/questions.jsonl`; base vectorial persistente en `chroma_db/`; resultados en `evals/results/`. `.env` contiene configuración local y credenciales, y no se versiona.

**Pruebas**: pytest; las llamadas al modelo Anthropic se simulan en todas las pruebas automatizadas.

**Plataforma objetivo**: servicio Python local en macOS y Linux. Los embeddings se ejecutan localmente; la generación requiere acceso al servicio de Anthropic.

**Tipo de proyecto**: servicio web pequeño con procesos locales de ingesta y evaluación.

**Objetivos de rendimiento**: sin SLA inicial de latencia o concurrencia. La evaluación registra duración y configuración para establecer una línea base; un SLA futuro requerirá mediciones y actualización de alcance.

**Restricciones**: única fuente admisible: Reglamento oficial en español; entrada no vacía de hasta 1.000 caracteres; `k=5` por defecto y configurable; las citas solo son válidas si pertenecen a fragmentos recuperados. No registrar preguntas ni credenciales.

**Escala/alcance**: una norma, interfaz en español, sin cuentas ni historial; corpus limitado al Reglamento y almacenamiento local.

## Verificación de la constitución

*Gate: aprobado antes de investigar y revisado después del diseño.*

- [x] Las afirmaciones se limitan a fragmentos recuperados del Reglamento; las citas son exactas, se muestran junto con la evidencia y la falta de respaldo produce abstención.
- [x] Las respuestas incluyen el aviso de orientación informativa, no asesoramiento jurídico.
- [x] Cambios en fragmentación, recuperación o prompt requieren evaluación versionada y resultados registrados, incluidos los casos no respondibles.
- [x] Cada módulo tendrá tests; las llamadas a Anthropic se simularán; pytest debe pasar antes de completar tareas.
- [x] Credenciales en variables de entorno, preguntas fuera de logs y entradas validadas.
- [x] Responsabilidades separadas para ingesta, recuperación, generación, API y evaluación; las dependencias corresponden a los requisitos y no añaden abstracciones innecesarias.
- [x] Código, símbolos y comentarios en inglés; especificaciones y documentación en español; un commit identificable por tarea y decisiones técnicas documentadas.

El límite de 1.000 caracteres del plan técnico reemplaza el supuesto provisional de 2.000; la especificación se sincronizó en FR-008 y Supuestos.

## Estructura del proyecto

### Documentación de esta funcionalidad

```text
specs/001-asistente-consulta-ai-act/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── openapi.yaml
```

### Código fuente y datos (raíz del repositorio)

```text
src/consulta_ai_act/
├── ingestion/       # Parseo y fragmentación del Reglamento oficial
├── retrieval/       # Embeddings y consulta de Chroma
├── generation/      # Prompt, cliente Anthropic y validación de citas
├── api/             # Rutas FastAPI, esquemas y página HTML
└── evaluation/      # Dataset, métricas e informes

scripts/
├── ingest_regulation.py
└── evaluate.py

data/
├── raw/              # HTML oficial; no se modifica durante la ingesta
└── eval/questions.jsonl

chroma_db/            # Índice regenerable; excluido de Git
evals/results/        # Informes reproducibles versionados
tests/
├── unit/
├── integration/
└── contract/
docs/decisions/       # Decisiones técnicas y alternativas descartadas
pyproject.toml
uv.lock
README.md
.env.example
```

**Decisión de estructura**: paquete único bajo `src/consulta_ai_act/`, con subpaquetes por responsabilidad y scripts delgados para ingesta y evaluación. No se crean servicios independientes ni capas de abstracción sin necesidad demostrada.

## Fase 0: Investigación y decisiones

Las decisiones y alternativas se detallan en [research.md](research.md). Se selecciona `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`: admite español y más de 50 idiomas y es más ligero que la variante multilingual MPNet. El conjunto de evaluación permitirá reemplazarlo si `recall@5` resulta insuficiente. El mismo modelo se configura explícitamente al ingerir y consultar. Chroma usa `PersistentClient` con `chroma_db/`.

El operador guarda el HTML oficial de EUR-Lex antes de la ingesta; el parser procesa el archivo local, no contenido de red variable en cada ejecución. FastAPI sirve `/ask`, `/health` y la página HTML. Anthropic se invoca mediante su SDK oficial y Messages API; el modelo y la clave son variables de entorno obligatorias, sin credenciales o valores secretos en código.

**Riesgo de extracción**: el HTML de EUR-Lex puede cambiar de estructura. El parser reconocerá encabezados de sección y fallará de forma cerrada si faltan secciones esperadas; tendrá fixtures. La ingesta conservará identificador CELEX, URL, fecha/versión y hash de origen. El parseo del HTML oficial real se verificará durante la implementación antes de aceptar el índice.

**Decisiones**:

- Un fragmento por considerando, artículo y anexo; los artículos largos se subdividen por apartado y conservan una referencia jurídica canónica más un identificador de fragmento único.
- `k=5` es el valor por defecto de recuperación, configurable por entorno o configuración validada.
- `recall@5` cuenta las referencias esperadas presentes en los cinco primeros fragmentos recuperados, dividido por el total de referencias esperadas.
- La cita se normaliza como `[Artículo 6]`, `[Considerando 12]` o `[Anexo III]`; la validación compara tipo y número normalizados con los metadatos de los fragmentos recuperados.
- Una cita inválida impide entregar el texto generado, registra un error estructurado sin pregunta ni respuesta completa y devuelve un error genérico seguro; no se añade un segundo intento de generación con coste.
- Los informes de evaluación incluyen fecha UTC, versión/hash del dataset, configuración (modelo de embeddings, `k`, modelo generativo y parámetros no secretos) y métricas.
- El límite de entrada es 1.000 caracteres, sustituyendo el supuesto preliminar de 2.000 de la especificación inicial.
- No se establece SLA de latencia ni disponibilidad para la primera versión; se conservarán mediciones como línea base.
- La API usa `langdetect` con semilla fija: acepta español solo si la probabilidad detectada es
    >=0,80; rechaza otros idiomas y entradas ambiguas antes de llamar a Anthropic. La detección no
    decide contenido jurídico ni permite que el modelo traduzca una consulta no admitida.
- La abstención usa un umbral de similitud configurable; se registra la configuración y se calibra
    en el dataset etiquetado, no se inventa un valor universal. No se genera una respuesta si ningún
    resultado supera el umbral.

## Fase 1: Diseño y contratos

- [Modelo de datos](data-model.md): fuente, fragmentos, consulta/respuesta, caso y ejecución de evaluación.
- [Contrato de API](contracts/openapi.yaml): esquemas de `/ask` y `/health`.
- [Guía de validación](quickstart.md): instalación, ingesta, servicio, tests y evaluación.

### Verificación de la constitución posterior al diseño

- [x] Solo los fragmentos recuperados forman el contexto de generación; el validador acepta citas únicamente si corresponden a esos fragmentos y no devuelve texto inválido.
- [x] La API devuelve respuesta, referencias, fragmentos usados y aviso legal; se abstiene si falta evidencia suficiente.
- [x] El dataset contiene preguntas respondibles y no respondibles; los informes incluyen `recall@5`, validez de citas y rechazo correcto, con versión, configuración y fecha.
- [x] Pruebas unitarias, de integración y contrato simulan Anthropic y no requieren llamadas pagadas.
- [x] Entrada limitada a 1.000 caracteres; logs estructurados sin preguntas, secretos ni respuestas completas; `.env` excluido de Git.
- [x] Modelos y almacenamiento local usan interfaces sencillas; los módulos están separados según el árbol de estructura.
- [x] README y artefactos de diseño en español; identificadores y comentarios de código en inglés; decisiones en `docs/decisions/` y un commit por tarea.

**Gate posterior al diseño**: aprobado, sin excepciones constitucionales pendientes.

## Seguimiento de complejidad

No se proponen violaciones de la constitución ni dependencias de arquitectura adicionales. Las dependencias enumeradas corresponden a requisitos funcionales concretos; si una decisión posterior añade complejidad, deberá justificarse y documentar alternativas.
