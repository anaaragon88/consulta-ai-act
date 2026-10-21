# Investigación técnica: Asistente de consulta del AI Act

**Fecha**: 2026-10-20

## Python y gestión del proyecto

- **Decisión**: Python 3.11+ con uv, `pyproject.toml` y `uv.lock` versionado.
- **Justificación**: uv gestiona proyecto, entorno, ejecución y lockfile reproducible.
- **Alternativas consideradas**: pip con requirements sin lock y Poetry. Se elige uv por ser la
  herramienta solicitada y reducir herramientas de gestión.
- **Fuente**: [Guía oficial de proyectos uv](https://docs.astral.sh/uv/guides/projects/).

## Ingesta y estructura documental

- **Decisión**: el operador coloca el HTML oficial español de EUR-Lex en `data/raw/`; la ingesta
  procesa archivos locales. Extraer identificador CELEX, URL, versión/fecha y hash SHA-256 del
  archivo fuente. Analizar la estructura del reglamento y generar fragmentos identificables por
  fuente, tipo de unidad, número, apartado (si aplica) e índice. Cada fragmento incluye texto
  exacto, referencia canónica y título si existe.
- **Justificación**: no depender de red durante la indexación evita que una descarga cambiante
  altere silenciosamente el corpus. El identificador de fragmento distingue apartados de un mismo
  artículo; la referencia canónica conserva la cita jurídica requerida.
- **Alternativas consideradas**: descarga automática en cada ingesta y fragmentación por longitud
  arbitraria. Se descartan por menor reproducibilidad y porque pueden separar unidades jurídicas.
- **Riesgo**: no se pudo extraer contenido significativo del HTML de EUR-Lex con el lector web
  utilizado durante esta investigación. El parser debe probarse contra el HTML oficial real y
  fixtures locales antes de aceptar la indexación. Si la estructura cambia o faltan secciones, la
  ingesta debe fallar explícitamente, no indexar un corpus parcial.

## Embeddings

- **Decisión**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, local, configurado
  por identificador de modelo. Usar exactamente el mismo modelo en ingesta y consulta.
- **Justificación**: la documentación de Sentence Transformers identifica el modelo como
  multilingüe para más de 50 idiomas, incluido español; es más compacto que multilingual MPNet.
  El rendimiento específico en lenguaje regulatorio se decidirá con el dataset y `recall@5`.
- **Alternativas consideradas**: `paraphrase-multilingual-mpnet-base-v2`, de mayor tamaño, y
  `distiluse-base-multilingual-cased-v2`, multilingüe con menor rendimiento general reportado en
  la tabla de benchmarks consultada.
- **Fuente**: [Modelos preentrenados de Sentence Transformers](https://sbert.net/docs/sentence_transformer/pretrained_models.html).

## Base vectorial

- **Decisión**: Chroma `PersistentClient` con el directorio local `chroma_db/`; persistir texto y
  metadatos por fragmento. Documentar métrica de distancia e identificador del modelo. El índice
  puede regenerarse desde el HTML y queda excluido de Git.
- **Justificación**: el cliente persistente local carga y guarda automáticamente los datos en la
  ruta indicada, adecuado para un solo reglamento y sin servidor adicional.
- **Alternativas consideradas**: base gestionada/remota (coste y complejidad innecesarios), índice
  efímero y búsqueda vectorial artesanal.
- **Fuente**: [Clientes de Chroma](https://docs.trychroma.com/docs/run-chroma/clients).

## Recuperación y métrica

- **Decisión**: recuperar `k=5` por defecto, configurable y limitado a un rango positivo; nunca
  superar el número de fragmentos disponibles. `recall@5` mide referencias esperadas presentes en
  los cinco primeros fragmentos, dividido por el total de referencias esperadas del caso. Las
  referencias repetidas cuentan una sola vez. Casos no respondibles se excluyen del denominador de
  recall y se miden en rechazo correcto.
- **Justificación**: fija una definición no ambigua y aplica las decisiones registradas en
  `/speckit-clarify`.
- **Alternativas consideradas**: recall binario por caso (pierde distinción si hay varias
  referencias) y contar solo citas de la respuesta (no mide recuperación independiente).

## Validación del idioma

- **Decisión**: `langdetect` con semilla fija para una clasificación reproducible antes de la
  generación; aceptar español solo si su probabilidad detectada es >=0,80 y rechazar otros idiomas
  o entradas ambiguas. Aplicar esta decisión solo al idioma de entrada, nunca para inferir el
  contenido jurídico.
- **Justificación**: la especificación requiere rechazar entradas en idiomas distintos del español;
  sin clasificación explícita, el comportamiento dependería del modelo generativo y su prompt.
- **Alternativas consideradas**: heurísticas manuales (frágiles para preguntas cortas y términos
  compartidos) y enviar entradas de idioma desconocido al modelo (no garantiza el límite de idioma).
- **Limitación**: consultas muy cortas pueden ser ambiguas para cualquier detector; con probabilidad
  de español inferior a 0,80, pedir reformular en español en vez de producir respuesta normativa.

## Generación y validación de citas

- **Decisión**: SDK oficial de Anthropic para Python y Messages API. Cliente inicializado al iniciar
  el servicio; modelo y `ANTHROPIC_API_KEY` requeridos desde el entorno. El prompt delimita el
  contexto recuperado como datos, prohíbe seguir instrucciones contenidas en él, obliga a responder
  solo desde el Reglamento y usa una frase fija de abstención.
- **Validación**: extraer referencias con gramática acotada para artículo, considerando y anexo;
  normalizar tipo y número romano/arábigo; comprobar cada cita contra metadatos de los fragmentos
  recuperados. Si una cita no está respaldada, no devolver el texto generado, registrar un error
  estructurado sin pregunta ni respuesta completa y devolver un error genérico seguro. No se añade
  un segundo intento de generación con coste.
- **Justificación**: SDK oficial y validación determinista separan la llamada generativa de la
  comprobación verificable de referencias.
- **Alternativas consideradas**: wrappers de agentes y compatibilidad con OpenAI; se descartan para
  reducir abstracciones y usar el SDK solicitado.
- **Fuente**: [SDKs oficiales de Anthropic](https://platform.claude.com/docs/en/api/client-sdks).

## API y página HTML

- **Decisión**: FastAPI con modelos Pydantic para validar solicitud/respuesta. `POST /ask` recibe
  pregunta y `k` opcional; salida contiene respuesta, referencias, fragmentos, aviso legal y estado
  de abstención. `GET /health` comprueba disponibilidad del proceso e índice sin exponer secretos.
  La aplicación sirve una página HTML estática mínima.
- **Justificación**: FastAPI valida y documenta contratos desde los modelos de solicitud y ofrece
  `TestClient` para pytest sin servicios reales.
- **Alternativas consideradas**: frontend independiente y framework web más completo; innecesarios
  para una página mínima y un único servicio.
- **Fuentes**: [Cuerpos de solicitud FastAPI](https://fastapi.tiangolo.com/tutorial/body/),
  [pruebas FastAPI](https://fastapi.tiangolo.com/tutorial/testing/).

## Evaluación y registro

- **Decisión**: `data/eval/questions.jsonl` versionado, con al menos 12 casos y al menos 3 preguntas
  marcadas no respondibles. El evaluador mide `recall@5`, tasa de citas válidas y rechazo correcto.
  El informe JSON incluye fecha UTC, versión/hash del dataset, embedding, `k`, modelo de generación
  y parámetros no secretos.
- **Justificación**: el formato favorece reproducibilidad y comparación objetiva de cambios.
- **Alternativas consideradas**: juicio subjetivo o resultados sin versión/configuración; no
  permiten atribuir cambios ni verificar mejoras.

## Pruebas, seguridad y privacidad

- **Decisión**: pytest por unidad, integración y contrato. Simular siempre Anthropic; no usar red en
  tests. Aislar Chroma y embeddings de prueba con directorio temporal o dobles deterministas cuando
  no se esté probando la integración de almacenamiento. Validar preguntas de hasta 1.000 caracteres.
  No registrar preguntas, prompts, respuestas completas, claves o cabeceras sensibles. Excluir
  `.env`, `.venv/`, `chroma_db/` y cachés de modelos de Git; `.env.example` contendrá nombres de
  variables y valores vacíos/no secretos.
- **Decisión pendiente de despliegue**: no se ha definido hosting, disponibilidad, autenticación de
  API ni retención de telemetría. La entrega es local y no debe exponerse a una red no confiable sin
  una decisión de seguridad posterior.
