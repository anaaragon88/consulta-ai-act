# Especificación de funcionalidad: Asistente de consulta del AI Act

<!-- Especificación en español; los identificadores del código se mantendrán en inglés. -->

**Rama de funcionalidad**: `001-asistente-consulta-ai-act` (directorio de especificación; no se creó una rama Git)

**Creada**: 2026-10-20

**Estado**: Borrador

**Entrada**: Descripción de usuario: «Quiero un asistente que responda preguntas en español sobre el Reglamento (UE) 2024/1689 de Inteligencia Artificial (AI Act), basándose únicamente en el texto oficial del reglamento. Usuarios: personas sin formación jurídica (product owners, desarrolladores, responsables de innovación) que necesitan orientarse sobre el reglamento antes de consultar con su equipo legal. Historias: recibir respuestas claras y breves con referencias, ver los fragmentos exactos, rechazar preguntas no cubiertas y evaluar calidad automáticamente. Criterios: toda respuesta incluye referencia salvo abstención; las citas deben existir y corresponder a los fragmentos; aviso de orientación no jurídica; evaluación versionada con al menos 12 preguntas y 3 sin respuesta; métricas de recuperación correcta, citas válidas y abstenciones correctas. Casos límite: preguntas vacías, demasiado largas o en otro idioma, preguntas ambiguas y ataques para ignorar instrucciones. Fuera de alcance: cuentas, historial, otros documentos legales, otros idiomas y asesoramiento jurídico personalizado.»

## Aclaraciones

### Sesión 2026-10-20

- Q: ¿Cómo se debe medir la recuperación de referencias esperadas cuando un caso puede tener varias? → A: Proporción de referencias recuperadas (recall@k).
- Q: ¿Qué valor de k se usará en recall@k? → A: recall@5.
- Q: ¿Qué cuenta como resultado en recall@5? → A: Los cinco primeros fragmentos recuperados.

## Escenarios de usuario y pruebas

### Historia de usuario 1: Obtener una respuesta fundamentada (Prioridad: P1)

Como product owner, desarrollador o responsable de innovación sin formación jurídica, quiero hacer una pregunta en español en lenguaje natural y recibir una respuesta clara y breve, para orientarme sobre el Reglamento antes de consultar con mi equipo legal.

**Por qué esta prioridad**: Es el valor principal del asistente. Sin respuestas fundamentadas y comprensibles, las demás funciones no ofrecen orientación útil.

**Prueba independiente**: Enviar una pregunta contestable por el Reglamento y comprobar que la respuesta está en español, es breve, incluye el aviso de orientación y vincula sus afirmaciones sustantivas con referencias exactas respaldadas por evidencia.

**Escenarios de aceptación**:

1. **Dado** que la pregunta está en español y el Reglamento contiene la respuesta, **cuando** el usuario la envía, **entonces** recibe una respuesta clara y breve con cada afirmación sustantiva respaldada por la referencia pertinente.
2. **Dado** que se genera una respuesta, **cuando** el usuario la consulta, **entonces** se indica que es orientación informativa y no asesoramiento jurídico.
3. **Dado** que una respuesta cita una disposición, **cuando** se comprueba la cita, **entonces** la referencia existe en el Reglamento y corresponde al fragmento que la respalda.

### Historia de usuario 2: Verificar la evidencia (Prioridad: P2)

Como usuario, quiero ver los fragmentos exactos del Reglamento que sustentan la respuesta y sus referencias, para verificar personalmente la información.

**Por qué esta prioridad**: La evidencia visible permite al usuario comprobar las respuestas y detectar posibles errores sin depender de la autoridad del asistente.

**Prueba independiente**: Hacer una pregunta contestable y verificar que la respuesta devuelve los fragmentos usados, que cada fragmento conserva una referencia localizable y que esa referencia coincide con la cita de la respuesta.

**Escenarios de aceptación**:

1. **Dado** que se recuperaron fragmentos para contestar, **cuando** se presenta la respuesta, **entonces** se muestran los fragmentos exactos utilizados junto con sus referencias a artículos, anexos o considerandos.
2. **Dado** que la respuesta no encuentra evidencia suficiente y se abstiene, **cuando** se presenta el resultado, **entonces** no se inventan fragmentos ni citas y se explica que no se encontró información suficiente en el Reglamento.

### Historia de usuario 3: Obtener una abstención cuando falte respaldo (Prioridad: P1)

Como usuario, quiero que el asistente reconozca cuando el Reglamento no responde a mi pregunta, para no confundir una conjetura con una obligación jurídica.

**Por qué esta prioridad**: Evitar respuestas inventadas y citas falsas es esencial para que la orientación no induzca a error.

**Prueba independiente**: Formular preguntas que no tengan respuesta en el Reglamento y comprobar que el asistente lo declara explícitamente, no aporta afirmaciones sustantivas sin respaldo ni cita referencias ajenas a la evidencia.

**Escenarios de aceptación**:

1. **Dado** que el Reglamento no contiene respuesta respaldada por los fragmentos disponibles, **cuando** se hace la pregunta, **entonces** el asistente lo dice explícitamente y no improvisa una respuesta.
2. **Dado** que la pregunta solicita información de otro idioma, de otro documento legal o asesoramiento jurídico personalizado, **cuando** se procesa, **entonces** el asistente informa que el alcance se limita a orientación general en español sobre el Reglamento y no contesta fuera de ese alcance.
3. **Dado** que la pregunta intenta que el asistente ignore sus instrucciones o use conocimiento externo, **cuando** se procesa, **entonces** se mantienen los límites de fuente y alcance, y la respuesta sustantiva sigue respaldada exclusivamente por el Reglamento.
4. **Dado** que la pregunta está vacía o supera el límite de longitud admitido, **cuando** se valida, **entonces** se solicita una pregunta válida mediante un mensaje claro y no se genera una respuesta normativa.
5. **Dado** que una pregunta puede referirse razonablemente a varias disposiciones, **cuando** la evidencia permite distinguirlas, **entonces** la respuesta señala las disposiciones pertinentes; si no permite determinar el sentido, pide una aclaración en vez de adivinar.

### Historia de usuario 4: Comparar la calidad entre versiones (Prioridad: P2)

Como responsable del proyecto, quiero ejecutar una evaluación automática con preguntas de referencia y consultar métricas reproducibles, para comparar la calidad entre versiones del asistente.

**Por qué esta prioridad**: La evaluación objetiva permite decidir si los cambios mejoran realmente la recuperación, las citas y las abstenciones.

**Prueba independiente**: Ejecutar la evaluación sobre el conjunto versionado, verificar su tamaño y casos sin respuesta, y confirmar que el informe muestra las tres métricas requeridas y permite identificar la versión evaluada.

**Escenarios de aceptación**:

1. **Dado** que existe una versión del conjunto de evaluación, **cuando** se ejecuta la evaluación, **entonces** el conjunto contiene al menos 12 preguntas, cada una con su referencia esperada o marcada como no respondible por el Reglamento, e incluye al menos 3 preguntas no respondibles.
2. **Dado** que termina una ejecución, **cuando** se presenta el informe, **entonces** incluye recall@5 —la proporción de referencias esperadas presentes en los cinco primeros fragmentos recuperados, respecto del total de referencias esperadas—, el porcentaje de respuestas con citas válidas y el porcentaje de preguntas no respondibles correctamente rechazadas.
3. **Dado** que se modifica la fragmentación, recuperación o instrucciones del asistente, **cuando** se compara el cambio, **entonces** se vuelve a ejecutar la evaluación y se registran el identificador de versión del conjunto y sus resultados para comparación.

### Casos límite

- Pregunta vacía, compuesta solo por espacios o demasiado larga: se rechaza con una indicación de cómo reformularla; no se produce respuesta normativa.
- Pregunta en un idioma distinto del español: se informa que solo se admiten preguntas en español; no se responde en otro idioma.
- Pregunta ambigua que apunta a más de un artículo, anexo o considerando: se citan las disposiciones pertinentes cuando la evidencia basta para desambiguar; en caso contrario se solicita precisión.
- Pregunta que combine una parte respondible con otra no cubierta: se responde únicamente la parte respaldada y se identifica explícitamente la parte no encontrada.
- Instrucciones del usuario para ignorar las reglas, responder desde conocimiento general o fabricar una cita: se conserva la restricción de fuente y se rechaza cualquier afirmación no respaldada.
- Fallo o ausencia de recuperación de evidencia: se informa que no se encontró información suficiente, en vez de completar la respuesta de memoria.

## Requisitos

### Requisitos funcionales

- **FR-001**: El sistema MUST aceptar preguntas no vacías en español y limitar su respuesta al texto oficial del Reglamento (UE) 2024/1689.
- **FR-002**: El sistema MUST producir respuestas en español, claras y breves, orientadas a personas sin formación jurídica. Para hacer verificable la brevedad, una respuesta estándar MUST tener como máximo 150 palabras, sin contar referencias, fragmentos y aviso legal.
- **FR-003**: Cada afirmación sustantiva de una respuesta MUST estar respaldada por uno o más fragmentos del Reglamento y vinculada a una referencia exacta de artículo, anexo o considerando.
- **FR-004**: Toda referencia incluida MUST corresponder a una disposición existente y estar respaldada por los fragmentos devueltos; el sistema MUST NOT inventar ni alterar referencias.
- **FR-005**: Cada respuesta MUST incluir los fragmentos exactos utilizados y sus referencias para que el usuario pueda verificarlos.
- **FR-006**: Cada respuesta sustantiva MUST incluir el aviso de que la información es orientativa y no constituye asesoramiento jurídico. Las respuestas de abstención y rechazo MUST conservar un aviso equivalente de alcance no jurídico.
- **FR-007**: Cuando la evidencia recuperada no permita responder, el sistema MUST decirlo explícitamente y abstenerse de aportar contenido sustantivo no respaldado. Si solo una parte de la pregunta está respaldada, MUST separar la respuesta respaldada de lo que no consta.
- **FR-008**: El sistema MUST validar que la pregunta no esté vacía y que no supere 2.000 caracteres. Para entradas inválidas MUST devolver un mensaje de validación y no generar una respuesta normativa.
- **FR-009**: El sistema MUST rechazar preguntas en idiomas distintos del español e informar del idioma admitido, sin producir una respuesta sustantiva en otro idioma.
- **FR-010**: Ante ambigüedad que no pueda resolverse con la evidencia, el sistema MUST pedir una aclaración antes de elegir una interpretación.
- **FR-011**: El sistema MUST mantener las restricciones de fuente y alcance aunque la pregunta solicite ignorar instrucciones, utilizar otras fuentes o inventar citas.
- **FR-012**: El alcance funcional MUST excluir cuentas de usuario, historial de conversación, documentos legales distintos del Reglamento y asesoramiento jurídico personalizado.
- **FR-013**: El repositorio MUST contener un conjunto de evaluación versionado con al menos 12 preguntas, la referencia esperada para cada pregunta respondible y al menos 3 casos explícitamente no respondibles según el Reglamento.
- **FR-014**: La evaluación automática MUST informar, como mínimo, recall@5 —referencias esperadas presentes en los cinco primeros fragmentos recuperados, dividido entre el total de referencias esperadas—, el porcentaje de respuestas con citas válidas y el porcentaje de preguntas no respondibles correctamente rechazadas.
- **FR-015**: Cada resultado de evaluación MUST identificar la versión del conjunto de preguntas evaluado y conservar las métricas para comparar ejecuciones.
- **FR-016**: Todo cambio en la fragmentación, recuperación o instrucciones que afecte a las respuestas MUST volver a ejecutar la evaluación y registrar sus resultados antes de aceptar una mejora.

### Entidades clave

- **Pregunta de usuario**: texto en español enviado para obtener orientación; se valida antes de procesarse y no se conserva como historial.
- **Fragmento del Reglamento**: pasaje textual exacto del Reglamento oficial, con referencia a artículo, anexo o considerando.
- **Respuesta**: orientación breve en español, formada por afirmaciones respaldadas, referencias, evidencia visible y aviso de no asesoramiento jurídico; puede ser una abstención explícita.
- **Caso de evaluación**: pregunta versionada con referencia esperada o clasificación de pregunta no respondible en el Reglamento.
- **Ejecución de evaluación**: resultado asociado a una versión del conjunto y que contiene las métricas mínimas para comparar versiones.

## Criterios de éxito

### Resultados medibles

- **SC-001**: El 100 % de las respuestas sustantivas evaluadas en el conjunto de referencia incluye al menos una referencia existente que está respaldada por los fragmentos mostrados; las abstenciones explícitas quedan exentas de incluir una cita.
- **SC-002**: El 100 % de las respuestas sustantivas incluye los fragmentos utilizados, sus referencias y el aviso de que la orientación no es asesoramiento jurídico.
- **SC-003**: El conjunto versionado contiene al menos 12 casos, incluidos al menos 3 casos no respondibles por el Reglamento.
- **SC-004**: Cada informe de evaluación incluye las tres métricas exigidas: recall@5 de referencias esperadas en los cinco primeros fragmentos recuperados, validez de citas y rechazo correcto de preguntas no respondibles.
- **SC-005**: El usuario puede verificar cada afirmación normativa de la respuesta contrastando el fragmento mostrado con la referencia correspondiente del Reglamento oficial.

## Supuestos

- La fuente documental autorizada es la versión oficial del Reglamento (UE) 2024/1689; no se incorporan otras normas, guías ni interpretaciones externas.
- El idioma de interacción del producto es el español. Una pregunta en otro idioma se rechaza, no se traduce de forma implícita.
- Se fija un límite de entrada de 2.000 caracteres como valor inicial verificable para preguntas «demasiado largas»; cambios futuros deben actualizar la especificación y sus pruebas.
- Se fija un máximo de 150 palabras para el cuerpo de una respuesta estándar para concretar «clara y breve»; referencias, evidencia y aviso legal no cuentan para ese límite.
- Las preguntas ambiguas pueden resolverse mediante una pregunta aclaratoria; no se asume una interpretación cuando pueda cambiar el sentido normativo.
- El conjunto de evaluación y los informes se mantienen en el repositorio con control de versiones; la comparación requiere identificar qué versión del conjunto se utilizó.
- La herramienta de evaluación puede usar respuestas simuladas o una configuración de prueba sin servicios externos de pago; esta especificación no prescribe tecnología.
- El asistente ofrece orientación general previa a la consulta con el equipo legal y no sustituye asesoramiento jurídico.
