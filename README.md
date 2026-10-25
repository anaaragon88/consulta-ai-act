# Asistente de consulta del AI Act

Asistente RAG para consultar en español el Reglamento (UE) 2024/1689 (AI Act). La API recupera fragmentos del texto oficial, genera respuestas fundamentadas y valida sus citas. Si no encuentra evidencia suficiente, se abstiene. Es una herramienta de orientación informativa y **no sustituye el asesoramiento jurídico**.

## Funcionalidades

- Ingesta local del texto oficial en español y creación de un índice vectorial persistente con Chroma.
- Recuperación semántica mediante embeddings locales (`intfloat/multilingual-e5-small`).
- API HTTP con endpoints para consultas y estado del índice.
- Validación de las citas frente a la evidencia recuperada.
- Pruebas automatizadas que simulan el servicio de generación.

## Requisitos

- macOS o Linux.
- Python 3.11 o superior.
- [uv](https://docs.astral.sh/uv/), para gestionar el entorno y las dependencias.
- Una clave de API de Anthropic para realizar consultas reales.

## Puesta en marcha

Desde la raíz del repositorio:

1. Instala las dependencias del proyecto:

   ```bash
   uv sync --dev
   ```

2. Crea la configuración local y añade tu clave de Anthropic a `.env`:

   ```bash
   cp .env.example .env
   ```

   Asigna tu clave a `ANTHROPIC_API_KEY`. El archivo `.env` no debe subirse a Git.

3. Descarga el HTML oficial en español del Reglamento (UE) 2024/1689 y guárdalo como `data/raw/regulation_es.html`. Por ejemplo, desde EUR-Lex:

   ```bash
   mkdir -p data/raw
   curl -L 'https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:32024R1689' -o data/raw/regulation_es.html
   ```

4. Construye el índice local a partir del archivo:

   ```bash
   uv run python -m scripts.ingest_regulation
   ```

   El índice se guarda en `chroma_db/`. La ingesta usa el HTML local y no lo descarga ni sustituye automáticamente.

5. Inicia la API:

   ```bash
   uv run uvicorn consulta_ai_act.api.app:app --reload
   ```

   Abre <http://127.0.0.1:8000/docs> para explorar y probar la API. El endpoint raíz no sirve una interfaz web.

Para detener el servidor, pulsa `Ctrl+C` en la terminal.

## Endpoints

- `GET /health`: comprueba si el índice vectorial está disponible.
- `POST /ask`: consulta el Reglamento.

Ejemplo de petición:

```bash
curl -X POST 'http://127.0.0.1:8000/ask' \
  -H 'Content-Type: application/json' \
  -d '{"question":"¿Qué establece el Reglamento?"}'
```

La respuesta incluye el texto generado, las referencias, los fragmentos de evidencia, un aviso legal y si el sistema se abstuvo.

## Pruebas

Ejecuta la suite automatizada con:

```bash
uv run pytest
```

Las pruebas no requieren una clave válida ni hacen llamadas pagadas al servicio de Anthropic.

## Configuración

La configuración se carga desde las variables de entorno o desde `.env`. Los valores disponibles están documentados en [.env.example](.env.example); incluyen el modelo de Anthropic, el modelo de embeddings, el número de resultados, la longitud máxima de pregunta y las rutas del índice y del Reglamento.

La clave de Anthropic es necesaria para responder consultas reales. El HTML fuente y el índice Chroma son artefactos locales ignorados por Git; cada persona que clone el proyecto debe obtener el HTML oficial y ejecutar la ingesta.

## Estructura

```text
src/consulta_ai_act/   Código de la API, ingesta, recuperación y generación
scripts/               Herramientas ejecutables del proyecto
data/raw/              HTML local de la normativa (no versionado)
data/debug/            Fragmentos exportados para depuración
chroma_db/              Índice vectorial local (no versionado)
tests/                  Pruebas unitarias, de integración y de contrato
specs/                  Especificación, diseño y contrato de API
```

Para más detalle sobre el alcance y las decisiones técnicas, consulta el [plan de implementación](specs/001-asistente-consulta-ai-act/plan.md), la [especificación](specs/001-asistente-consulta-ai-act/spec.md) y la [guía rápida](specs/001-asistente-consulta-ai-act/quickstart.md).
