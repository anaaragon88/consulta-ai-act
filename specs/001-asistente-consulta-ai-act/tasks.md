# Tareas: Asistente de consulta del AI Act

**Documentos de entrada**: `specs/001-asistente-consulta-ai-act/`

**Prerrequisitos**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/openapi.yaml` y `quickstart.md`.

**Pruebas**: cada módulo afectado requiere tests automatizados con pytest. Simular todas las llamadas a Anthropic; ningún test puede contactar servicios externos de pago. Cada tarea se completa solo cuando pasan los tests pertinentes. Cambios de fragmentación, recuperación o prompt requieren ejecutar y registrar la evaluación versionada.

**Organización**: fases por historia de usuario y prioridad. Los identificadores de historias corresponden a `spec.md`.

## Formato y rutas

- Cada tarea usa el formato `- [ ] TNNN [P?] [USn?] Descripción con ruta exacta`.
- `[P]` indica tareas independientes, en archivos distintos y sin dependencias pendientes.
- Las fases de setup/fundacionales y de cierre no llevan etiqueta de historia; cada tarea de historia lleva `[US1]`…`[US4]`.
- Código y comentarios en inglés; esta lista y la documentación en español.

## Fase 1: Preparación compartida

**Objetivo**: inicializar el paquete Python reproducible y proteger secretos y artefactos locales.

- [ ] T001 Crear `pyproject.toml` con Python >=3.11, dependencias de ejecución FastAPI, Chroma, sentence-transformers, SDK Anthropic, Beautiful Soup, python-dotenv y langdetect; añadir pytest y HTTPX como dependencias de desarrollo.
- [ ] T002 [P] Configurar `.gitignore` para excluir `.env`, `.venv/`, `chroma_db/`, cachés de modelos y artefactos temporales, conservando `data/eval/questions.jsonl` y `evals/results/`.
- [ ] T003 Crear `.env.example` con nombres de configuración no secreta y valores vacíos o de ejemplo no válidos; incluir `ANTHROPIC_API_KEY`, modelo generativo, modelo de embeddings, `RETRIEVAL_K` y ruta de Chroma.
- [ ] T004 Crear el paquete `src/consulta_ai_act/` y sus subpaquetes `ingestion/`, `retrieval/`, `generation/`, `api/` y `evaluation/`, con inicializadores mínimos.
- [ ] T005 Configurar pytest y rutas de importación del paquete en `pyproject.toml`; crear `tests/unit/`, `tests/integration/` y `tests/contract/` con archivos `__init__.py` solo si son necesarios para imports.

## Fase 2: Fundamentos bloqueantes

**Objetivo**: fijar configuración validada, tipos compartidos y manejo seguro de errores antes de las historias.

- [ ] T006 [P] Implementar configuración tipada y validada desde variables de entorno en `src/consulta_ai_act/config.py`, incluyendo límite de 1.000 caracteres, `k=5`, máximo configurable `k=20`, modelo generativo, modelo de embeddings y directorios.
- [ ] T007 [P] Definir tipos compartidos de fuente, fragmento, evidencia y respuesta en `src/consulta_ai_act/models.py`, manteniendo separados `chunk_id` y referencia jurídica canónica.
- [ ] T008 Crear logging estructurado y excepciones seguras en `src/consulta_ai_act/logging_config.py` y `src/consulta_ai_act/errors.py`; filtrar texto de preguntas, prompts, respuestas completas y credenciales.
- [ ] T009 Añadir tests fundacionales en `tests/unit/test_config.py`, `tests/unit/test_models.py` y `tests/unit/test_logging_config.py` para límites de configuración, metadatos y ausencia de datos sensibles en logs.
- [ ] T010 Crear fixtures HTML locales de prueba en `tests/fixtures/regulation_sample.html`, cubriendo considerando, artículo con apartados, título y anexo sin incluir credenciales ni depender de red.

**Punto de control**: configuración, tipos compartidos, privacidad de logs y fixtures están establecidos; ninguna historia debe duplicar estas bases.

## Fase 3: Historia de usuario 1 — Obtener una respuesta fundamentada (P1, MVP)

**Objetivo**: contestar preguntas con respuesta en el Reglamento, usando fragmentos oficiales, referencias válidas y aviso jurídico.

**Prueba independiente**: con el fixture y dependencias simuladas, enviar una pregunta contestable y verificar respuesta en español, citas que existen en los fragmentos de contexto, fragmentos devueltos y aviso no jurídico.

### Tests de la historia US1

- [ ] T011 [P] [US1] Probar extracción estructural, hash de fuente y fallo cerrado con HTML incompleto en `tests/unit/ingestion/test_html_parser.py`.
- [ ] T012 [P] [US1] Probar fragmentación exacta por considerando, artículo, apartados de artículos largos y anexos en `tests/unit/ingestion/test_chunker.py`.
- [ ] T013 [P] [US1] Probar generación local de embeddings, inserción idempotente en Chroma temporal y pipeline/script de ingesta con dependencias aisladas en `tests/integration/test_vector_index.py` y `tests/integration/test_ingestion_pipeline.py`.
- [ ] T014 [P] [US1] Probar recuperación `k=5` por defecto, `k` configurado y metadatos de referencia en `tests/unit/retrieval/test_retriever.py`.
- [ ] T015 [P] [US1] Probar prompt limitado al contexto, frase fija de abstención y respuesta en español con SDK Anthropic simulado en `tests/unit/generation/test_answer_generator.py`.
- [ ] T016 [P] [US1] Probar aceptación de citas respaldadas y rechazo de citas no presentes en contexto en `tests/unit/generation/test_citation_validator.py`.
- [ ] T017 [US1] Probar el contrato `POST /ask` para un caso respondible, incluyendo respuesta, referencias, fragmentos y aviso legal, con generación y recuperación simuladas en `tests/contract/test_ask_endpoint.py`.

### Implementación de US1

- [ ] T018 [US1] Obtener de EUR-Lex y guardar el HTML oficial español como `data/raw/regulation_es.html`; implementar parser local con identificación CELEX, metadatos de origen y error ante secciones ausentes en `src/consulta_ai_act/ingestion/html_parser.py`.
- [ ] T019 [US1] Implementar fragmentación estructural con `chunk_id`, `canonical_reference`, tipo, número, título, apartado, índice y hash en `src/consulta_ai_act/ingestion/chunker.py`.
- [ ] T020 [US1] Implementar script de ingesta que lee `data/raw/`, aplica el parser y fragmentador y actualiza el índice persistente en `scripts/ingest_regulation.py`.
- [ ] T021 [US1] Implementar adaptador local sentence-transformers y almacenamiento/consulta Chroma `PersistentClient` en `src/consulta_ai_act/retrieval/vector_store.py`.
- [ ] T022 [US1] Implementar recuperación top-k configurable con `k=5` predeterminado, retorno de fragmentos con metadatos y exposición de puntuación de relevancia para abstención calibrable en `src/consulta_ai_act/retrieval/retriever.py`.
- [ ] T023 [US1] Implementar cliente oficial Anthropic y prompt de respuesta únicamente desde contexto delimitado, con modelo y API key desde configuración en `src/consulta_ai_act/generation/answer_generator.py`.
- [ ] T024 [US1] Implementar normalización y validación determinista de citas contra referencias de fragmentos recuperados en `src/consulta_ai_act/generation/citation_validator.py`; no devolver respuesta con cita inválida.
- [ ] T025 [US1] Implementar servicio de consulta que conecta recuperación, generación y validación y construye respuesta con evidencia y aviso legal en `src/consulta_ai_act/answer_service.py`.
- [ ] T026 [US1] Implementar esquemas y rutas `POST /ask` con respuestas exitosas, manejo genérico seguro de fallos y dependencias inyectables en `src/consulta_ai_act/api/schemas.py` y `src/consulta_ai_act/api/routes.py`.
- [ ] T027 [US1] Ensamblar aplicación FastAPI y ciclo de vida de configuración/índice en `src/consulta_ai_act/api/app.py`.

**Punto de control**: una pregunta respondible se contesta desde el Reglamento y devuelve citas comprobadas, fragmentos exactos y aviso legal.

## Fase 4: Historia de usuario 3 — Abstenerse sin respaldo (P1)

**Objetivo**: rechazar consultas sin evidencia, entradas inválidas o solicitudes fuera de idioma/alcance, sin improvisar ni filtrar datos.

**Prueba independiente**: probar casos no respondibles, entradas vacías/largas, idioma no español, ambigüedad y ataques de instrucciones; verificar abstención o error seguro sin contenido no respaldado.

### Tests de la historia US3

- [ ] T028 [P] [US3] Probar validación de entrada vacía, solo espacios, >1.000 caracteres, `k` inválido, idioma español con confianza >=0,80, otro idioma y detección ambigua en `tests/unit/api/test_request_validation.py`.
- [ ] T029 [P] [US3] Probar frase exacta de abstención bajo el umbral de relevancia configurado y respuesta normal sobre el umbral en `tests/unit/generation/test_abstention.py`.
- [ ] T030 [P] [US3] Probar ataques de prompt injection, solicitudes de fuentes externas y pregunta ambigua sin evidencia suficiente en `tests/integration/test_scope_and_injection.py`, con modelo simulado.
- [ ] T031 [P] [US3] Probar que errores de cita, generador y validación no registran preguntas, prompts ni respuesta completa en `tests/integration/test_sensitive_logging.py`.
- [ ] T032 [US3] Probar `/health` disponible/no disponible y errores seguros de `/ask` en `tests/contract/test_health_endpoint.py` y `tests/contract/test_ask_errors.py`.

### Implementación de US3

- [ ] T033 [US3] Implementar validación con langdetect y semilla fija; aceptar idioma español solo con confianza >=0,80, rechazar otros/ambiguos, texto vacío/espacios y >1.000 caracteres en `src/consulta_ai_act/api/schemas.py` y `src/consulta_ai_act/api/language_validation.py`.
- [ ] T034 [US3] Implementar abstención constante cuando la mejor puntuación de recuperación queda por debajo del umbral configurable, separar partes respondibles/no respondibles y registrar el umbral en resultados de evaluación en `src/consulta_ai_act/generation/answer_generator.py`, `src/consulta_ai_act/answer_service.py` y `src/consulta_ai_act/config.py`.
- [ ] T035 [US3] Endurecer instrucciones contra prompt injection y tratar el contexto recuperado como datos, no instrucciones, en `src/consulta_ai_act/generation/answer_generator.py`.
- [ ] T036 [US3] Implementar respuestas HTTP seguras para entrada inválida, cita no válida, fallo de Anthropic e índice ausente en `src/consulta_ai_act/api/routes.py` y `src/consulta_ai_act/errors.py`.
- [ ] T037 [US3] Implementar `GET /health` con estado del proceso e índice sin exponer configuración ni secretos en `src/consulta_ai_act/api/routes.py`.

**Punto de control**: el usuario recibe un rechazo/abstención clara y segura siempre que no haya respaldo suficiente o la entrada esté fuera de alcance.

## Fase 5: Historia de usuario 2 — Verificar la evidencia (P2)

**Objetivo**: permitir que la persona usuaria inspeccione las citas y los fragmentos exactos empleados por cada respuesta.

**Prueba independiente**: abrir la interfaz HTML, enviar una pregunta respondible y comprobar que muestra la respuesta, el aviso, referencias y texto exacto de cada evidencia; confirmar que una abstención no presenta citas fabricadas.

### Tests de la historia US2

- [ ] T038 [P] [US2] Probar que la respuesta HTTP serializa cada fragmento exacto, referencia y aviso legal en `tests/contract/test_evidence_response.py`.
- [ ] T039 [P] [US2] Probar la página HTML y los estados de carga, respuesta, abstención y error con API simulada en `tests/integration/test_web_interface.py`.

### Implementación de US2

- [ ] T040 [US2] Crear interfaz HTML accesible en español con formulario, contador/límite de 1.000 caracteres y estados de envío/error en `src/consulta_ai_act/api/static/index.html`.
- [ ] T041 [US2] Renderizar respuesta, aviso legal, referencias y panel expandible con fragmentos exactos escapados como texto en `src/consulta_ai_act/api/static/app.js` y `src/consulta_ai_act/api/static/styles.css`.
- [ ] T042 [US2] Servir la página estática desde FastAPI y conectar el formulario a `POST /ask` en `src/consulta_ai_act/api/routes.py` y `src/consulta_ai_act/api/app.py`.

**Punto de control**: el contenido normativo y sus fragmentos de respaldo son inspeccionables en la interfaz, sin convertir evidencia en HTML ejecutable.

## Fase 6: Historia de usuario 4 — Comparar calidad entre versiones (P2)

**Objetivo**: mantener un benchmark versionado y generar informes comparables con recall@5, citas válidas y rechazos correctos.

**Prueba independiente**: ejecutar el evaluador con dependencias deterministas/simuladas y confirmar al menos 12 casos, 3 no respondibles, métricas correctas e informe con fecha y configuración no secreta.

### Tests de la historia US4

- [ ] T043 [P] [US4] Probar carga y validación de JSONL, identificadores únicos, referencias esperadas y mínimos de 12 casos/3 no respondibles en `tests/unit/evaluation/test_dataset.py`.
- [ ] T044 [P] [US4] Probar recall@5 por referencias, tasa de citas válidas y tasa de rechazo correcto, incluidos denominadores vacíos, en `tests/unit/evaluation/test_metrics.py`.
- [ ] T045 [P] [US4] Probar informe fechado, runner y comando CLI con configuración/dataset identificables y sin secretos ni preguntas en `tests/integration/test_evaluation_report.py` y `tests/integration/test_evaluation_cli.py`.
- [ ] T046 [US4] Crear `data/eval/questions.jsonl` versionado con al menos 12 preguntas validadas contra el Reglamento, referencias esperadas en respondibles y al menos 3 no respondibles; evitar datos personales.

### Implementación de US4

- [ ] T047 [US4] Implementar esquema y carga del dataset JSONL con validación de invariantes y versión/hash en `src/consulta_ai_act/evaluation/dataset.py`.
- [ ] T048 [US4] Implementar métricas de recall@5 calculado sobre los cinco primeros fragmentos, validez de citas y rechazo correcto en `src/consulta_ai_act/evaluation/metrics.py`.
- [ ] T049 [US4] Implementar ejecución sobre todos los casos usando el servicio de consulta y captura sin persistir preguntas/respuestas individuales en `src/consulta_ai_act/evaluation/runner.py`.
- [ ] T050 [US4] Implementar escritura atómica de informe JSON en `evals/results/` con fecha UTC, hash/versionado de preguntas, configuración no secreta y métricas en `src/consulta_ai_act/evaluation/report.py`.
- [ ] T051 [US4] Crear comando reproducible para lanzar la evaluación y fallar si falta el dataset mínimo o una métrica obligatoria en `scripts/evaluate.py`.

**Punto de control**: la evaluación muestra las tres métricas acordadas y deja resultados identificables para comparar cambios.

## Fase 7: Cierre y preocupaciones transversales

**Objetivo**: documentar el uso real, decisiones, validación y calidad final.

- [ ] T052 [P] Documentar instalación, variables de entorno, carga del HTML oficial, ingesta, ejecución local, interfaz, tests y evaluación en `README.md`.
- [ ] T053 [P] Documentar la elección del modelo de embeddings, Chroma local, fragmentación, validación de citas y alternativas descartadas en `docs/decisions/001-diseno-rag.md`.
- [ ] T054 Actualizar `specs/001-asistente-consulta-ai-act/quickstart.md` con comandos reales y ejecutar sus escenarios tras implementar API, ingesta y evaluación.
- [ ] T055 Ejecutar `uv run pytest` sobre `tests/` y corregir todos los fallos antes de cerrar la funcionalidad.
- [ ] T056 Ejecutar el benchmark final tras cambios en fragmentación, recuperación o prompt y guardar resultados revisables en `evals/results/`.
- [ ] T057 Revisar que `.env` no esté versionado, que logs no incluyan preguntas/secretos/respuestas completas y que entradas/citas inválidas fallen de forma segura en `src/consulta_ai_act/` y la configuración Git.
- [ ] T058 Crear en `.git/` un commit identificable por cada tarea completada, con mensaje que indique su ID y propósito.

## Dependencias y orden de ejecución

### Dependencias por fase

- **Preparación (Fase 1)**: T001–T005; T002 y T003 pueden ejecutarse en paralelo. La estructura de paquete y pytest depende de T001.
- **Fundamentos (Fase 2)**: T006–T010 después del setup; T006, T007 y T010 son paralelizables; logging/tests dependen de las interfaces definidas.
- **US1 (Fase 3)**: depende de setup y fundamentos. Tests independientes por componente pueden prepararse en paralelo; parser precede al chunker; chunker precede a ingesta/vectorización; índice precede a recuperación y servicio; generación y validador preceden a `/ask` integrado.
- **US3 (Fase 4)**: depende de US1 porque endurece el flujo y valida abstención sobre la recuperación y generación reales; tests separados pueden ejecutarse en paralelo.
- **US2 (Fase 5)**: depende del contrato estable de `/ask` y la serialización de evidencia de US1; interfaz se integra con la API.
- **US4 (Fase 6)**: el dataset y tests de métricas pueden prepararse en paralelo con US2; el runner requiere el servicio de US1 y la abstención de US3; ejecución final requiere el dataset completo.
- **Cierre (Fase 7)**: depende de las historias incluidas en la entrega; benchmark final siempre va después del último cambio de recuperación o prompt.

### Orden de historias

- **US1 (P1)**: primera entrega útil, con respuesta respaldada y citas validadas.
- **US3 (P1)**: requiere el pipeline de US1 para garantizar abstención segura.
- **US2 (P2)**: presenta la evidencia ya incluida en el contrato de US1.
- **US4 (P2)**: compara calidad de una implementación funcional; la preparación del dataset puede adelantarse.

## Oportunidades de paralelización

- Setup: T002 y T003 en paralelo; luego paquete/pytest T004–T005.
- Fase fundacional: configuración T006, tipos T007 y fixture HTML T010 en paralelo; logging T008 y sus pruebas T009 siguen la definición de interfaces.
- US1: pruebas de parser/chunker/retrieval/generación/citas (T011–T016) en archivos distintos; implementación se integra según dependencias, no todas al mismo tiempo.
- US3: validación de entrada, abstención, prompt injection y privacidad (T028–T031) en paralelo una vez disponibles los módulos de US1.
- US4: pruebas de dataset/métricas/informe (T043–T045) y elaboración del dataset T046 pueden realizarse en paralelo; runner requiere las interfaces de métricas y servicio.
- Pulido: README y decisión técnica (T052–T053) en paralelo; validación quickstart y benchmark final secuenciales tras el código.

### Ejemplo paralelo: US1

```text
T011 tests del parser en tests/unit/ingestion/test_html_parser.py
T014 tests del recuperador en tests/unit/retrieval/test_retriever.py
T015 tests del generador en tests/unit/generation/test_answer_generator.py
T016 tests del validador en tests/unit/generation/test_citation_validator.py
```

### Ejemplo paralelo: US4

```text
T043 tests de dataset en tests/unit/evaluation/test_dataset.py
T044 tests de métricas en tests/unit/evaluation/test_metrics.py
T046 dataset versionado en data/eval/questions.jsonl
```

## Estrategia de implementación

### MVP primero (US1)

1. Completar setup y fundamentos.
2. Completar ingesta estructural, Chroma y recuperación.
3. Completar generación con Anthropic simulado en pruebas y validación determinista de citas.
4. Completar `POST /ask` con respuesta, referencias, fragmentos exactos y aviso legal.
5. Verificar de forma independiente pregunta respondible y cobertura de tests de los módulos MVP.

La abstención segura de US3 sigue siendo obligatoria por la constitución y debe preceder a cualquier
uso externo del MVP; la división por historias no autoriza respuestas sin respaldo.

### Entrega incremental

1. Setup + fundamentos → entorno reproducible.
2. US1 → respuesta fundamentada y contrato API.
3. US3 → abstención, validaciones, alcance y fallos seguros.
4. US2 → inspección de evidencia desde la interfaz HTML.
5. US4 → benchmark y comparación de versiones.
6. Pulido → documentación, revisión de privacidad, tests y evaluación final.

## Notas de cierre

- Cada descripción accionable identifica archivo(s) concretos y función observable.
- Las métricas de evaluación se vuelven a ejecutar tras cualquier modificación de fragmentación, recuperación o prompt.
- Una cita inválida nunca se entrega a la persona usuaria; el registro técnico no contiene la pregunta.
- Crear commits identificables, idealmente uno por tarea, y documentar decisiones técnicas significativas.
