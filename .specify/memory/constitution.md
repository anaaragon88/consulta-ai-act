<!--
Informe de impacto y sincronización
- Cambio de versión: sin versión previa (constitución inicial) -> 1.0.0
- Principios modificados: ninguno; se establecen los siete principios indicados por la persona propietaria
- Secciones añadidas: Restricciones adicionales; Flujo de desarrollo y controles de calidad
- Secciones eliminadas: ninguna
- Plantillas: ✅ .specify/templates/plan-template.md; ✅ .specify/templates/spec-template.md;
	✅ .specify/templates/tasks-template.md
- Comandos: ⚠ .specify/templates/commands/ no existe; se revisaron el comando de extensión
	disponible y las instrucciones de ejecución, sin necesidad de actualizaciones específicas
- Pendiente: confirmar la fecha original de ratificación
-->
# Constitución de Consulta AI Act

## Principios fundamentales

### I. Fidelidad a la fuente
Toda afirmación sustantiva de una respuesta MUST estar respaldada por fragmentos recuperados del
Reglamento (UE) 2024/1689 y acompañada de la referencia exacta a su artículo, anexo o considerando.
El sistema MUST limitar sus respuestas al contenido de ese Reglamento. Si los fragmentos recuperados
no contienen la información necesaria, MUST decirlo explícitamente y abstenerse de completar la
respuesta con conocimiento externo. MUST NOT inventar ni alterar citas; una cita inventada es el
fallo más grave del sistema.

### II. Transparencia con quien pregunta
Cada respuesta MUST incluir los fragmentos utilizados y sus referencias para permitir su
verificación. También MUST indicar que ofrece orientación informativa y no asesoramiento jurídico.

### III. Calidad medible
El repositorio MUST mantener un conjunto de evaluación versionado con preguntas, referencias
esperadas y casos cuya respuesta no consta en el Reglamento. Todo cambio en fragmentación,
recuperación o prompt MUST volver a ejecutar la evaluación y registrar sus resultados. Una mejora
solo se acepta si las métricas acordadas la demuestran; la impresión subjetiva no es evidencia.

### IV. Tests antes de dar por terminada una tarea
Cada módulo MUST contar con tests automatizados pertinentes y todos los tests MUST pasar antes de
dar una tarea por terminada. Los tests MUST simular las llamadas al modelo de lenguaje y MUST NOT
invocar servicios externos de pago.

### V. Simplicidad
El diseño MUST elegir la solución más simple que cumpla la especificación, limitar dependencias y
evitar abstracciones sin una necesidad demostrada. Las responsabilidades MUST permanecer separadas
en módulos pequeños de ingesta, recuperación, generación y API. Una complejidad adicional requiere
justificación documentada.

### VI. Seguridad y privacidad
Las claves y credenciales MUST residir en variables de entorno y MUST NOT incluirse en el
repositorio. El sistema MUST validar las entradas de usuario y MUST NOT registrar en logs el texto
de las preguntas. Los cambios MUST preservar estas garantías.

### VII. Trazabilidad
Cada tarea MUST quedar asociada a un commit identificable, con un mensaje que describa la tarea.
Las decisiones técnicas relevantes y las alternativas descartadas MUST documentarse en el
repositorio para que puedan revisarse posteriormente.

## Restricciones adicionales

El código fuente, los nombres de símbolos y los comentarios MUST estar en inglés. Las
especificaciones, la documentación del proyecto y las respuestas dirigidas a usuarios MUST estar
en español. El alcance documental de las respuestas del asistente es exclusivamente el Reglamento
(UE) 2024/1689.

## Flujo de desarrollo y controles de calidad

Las tareas y sus criterios de aceptación MUST permitir comprobar el cumplimiento de los principios
aplicables. Los cambios que afecten a fragmentación, recuperación o prompt MUST incluir la ejecución
y el registro de la evaluación versionada. La revisión MUST confirmar tests aprobados, ausencia de
credenciales en el repositorio y ausencia de textos de preguntas en logs. La arquitectura MUST
mantener responsabilidades separadas para ingesta, recuperación, generación y API.

## Gobernanza

Esta constitución prevalece sobre cualquier otra decisión, práctica o documento del proyecto. Una
excepción no puede introducirse de forma tácita: requiere modificar la constitución. Toda enmienda
MUST explicar el motivo, actualizar la versión y la fecha de enmienda, y revisar los artefactos
dependientes para mantenerlos sincronizados. La versión sigue semver: MAJOR para cambios
incompatibles o redefiniciones de principios; MINOR para nuevos principios, secciones o requisitos
materiales; PATCH para aclaraciones y correcciones no semánticas. La fecha de ratificación conserva
la fecha de adopción original; si no se conoce, permanece marcada como pendiente de confirmación.
Cada tarea y cada revisión de diseño MUST verificar el cumplimiento de esta constitución, con
especial atención a fidelidad, privacidad, tests y trazabilidad. Las decisiones incompatibles
MUST documentar la excepción propuesta y no pueden darse por conformes sin una enmienda aprobada.

**Versión**: 1.0.0 | **Ratificada**: TODO(RATIFICATION_DATE): confirmar fecha original de adopción | **Última enmienda**: 2026-10-20
