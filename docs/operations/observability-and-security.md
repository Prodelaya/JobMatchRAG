# Base mínima de observabilidad y seguridad — JobMatchRAG

## 1. Propósito

Este documento fija el baseline mínimo de observabilidad y protección operativa para V1.

No define tooling, vendor ni runbooks exhaustivos. Define QUÉ debe poder verse, alertarse y protegerse para operar el sistema sin adivinar.

## 2. Base mínima de visibilidad operativa

La foundation exige visibilidad mínima sobre:

- runs de fuentes;
- errores relevantes y su clasificación;
- publicación y alertas de Telegram;
- uso y coste de capacidades LLM/chat;
- accesos y acciones sobre la superficie protegida.

La idea es simple: si el sistema falla, degrada o se usa de forma anómala, eso debe quedar visible sin depender de inspección manual ad hoc.

## 3. Métricas mínimas por capacidad

### 3.1 Ingesta y salud de los runs

Como mínimo, la operación debe poder observar:

- runs iniciados, completados, parciales y fallidos por fuente;
- duración por run y por fuente;
- volumen capturado por run;
- checkpoints de entrada/salida cuando existan;
- snapshot de capabilities y filter intent aplicado por run;
- errores `retryable` frente a `terminal`;
- retries ejecutados y agotados.

### 3.2 Matching, publicación y notificaciones

La operación debe poder ver, como mínimo:

- ofertas que pasaron o fallaron `eligibility`;
- distribución básica del score final;
- oportunidades nuevas publicadas;
- alertas de Telegram enviadas, fallidas o suprimidas por duplicación.

### 3.3 Recruiter chat y uso de LLM

Aunque recruiter chat sea secundario, su coste y salud deben ser visibles:

- volumen de consultas;
- consultas rechazadas por límites o falta de contexto permitido;
- errores de retrieval o generación;
- consumo/coste agregado de uso LLM/chat.

## 4. Base mínima de señales de alerta

La foundation deja cerradas señales mínimas de alerta, aunque los umbrales exactos se definan en verticales posteriores.

Se deben poder activar alertas cuando ocurra alguna de estas condiciones:

- una fuente acumula fallos o runs incompletos de forma sostenida;
- el pipeline deja de producir material publicable cuando debería haber actividad;
- Telegram empieza a fallar o a suprimir más de lo esperable;
- recruiter chat/LLM supera presión de coste o fiabilidad;
- la superficie protegida recibe accesos fallidos o actividad anómala.

## 5. Expectativas de audit trail

El sistema debe conservar un rastro auditable suficiente para responder:

- qué fuente o acción se ejecutó;
- quién o qué disparó la operación;
- cuándo empezó y terminó;
- qué capabilities y filtros del lado de la fuente se declararon/intentarion;
- con qué estado cerró;
- qué checkpoint y observaciones de rate limit dejó;
- qué errores relevantes ocurrieron;
- si hubo publicación o alerta derivada;
- si una acción fue administrativa y sobre qué superficie protegida ocurrió.

La trazabilidad no es opcional: sin eso no hay operación seria ni debugging confiable.

## 6. Controles de superficie protegida

### 6.1 Boundary de admin

Las acciones protegidas siguen estas reglas base:

- auth dedicada y separada de rutas públicas;
- superficie **MFA-ready** desde foundation;
- acceso solo a operaciones internas, nunca mezcladas con la experiencia pública;
- registro de intentos y acciones administrativas relevantes.

### 6.2 Base mínima frente a abuso público/chat

La foundation también deja cerrada una protección mínima sobre superficies expuestas:

- límites básicos de uso/rate limiting en superficies públicas o recruiter-facing;
- rechazo explícito cuando una consulta excede guardrails o sale del corpus permitido;
- visibilidad de rechazos, errores y abuso potencial sin exponer detalles sensibles públicamente.

El detalle fino de prompt-injection, umbrales exactos o políticas avanzadas vendrá después. La base mínima ya queda fijada.

## 7. Reglas de visibilidad de runs y errores

La operación debe poder seguir un run de punta a punta sin inspeccionar tablas crudas a ciegas.

Eso implica que la visibilidad mínima debe distinguir:

- fuente y contexto del run;
- `job_id` y `run_id` enlazables;
- estado final del run;
- etapa donde ocurrió el fallo;
- clase del error (`retryable` o `terminal`);
- retries agotados, checkpoints y observaciones relevantes de rate limit;
- impacto visible posterior: sin publicación, con publicación o con alerta de Telegram.

Los errores relevantes se conservan según la política de retención aceptada y deben quedar suficientemente contextualizados para diagnóstico posterior.

## 8. Disclosure público vs interno

La observabilidad completa es interna. La superficie pública solo debe mostrar señales generales de frescura/actividad.

No corresponde exponer públicamente:

- trazas operativas sensibles;
- errores internos completos;
- internals de seguridad o abuso;
- razones detalladas que faciliten explotación o interpretación incorrecta.

## 9. Relación con el foundation pack

Este documento complementa a:

- `docs/architecture/system-overview.md` para boundaries público/protegido y pipeline general;
- `docs/architecture/ingestion-and-sources.md` para runs, errores y trazabilidad por fuente;
- `docs/operations/policies-and-controls.md` para retención, backups, degradación y política base de seguridad;
- `docs/product/recruiter-chat.md` para el carácter secundario del chat y sus límites de corpus.

## 10. Qué deben reutilizar los cambios verticales futuros

Las próximas verticales deben reutilizar esta base sin reabrirla:

- observabilidad mínima de runs, errores, alertas y uso de LLM/chat;
- señales de alerta para salud, coste y abuso;
- audit trail suficiente de acciones administrativas y resultados operativos;
- controles explícitos sobre la superficie protegida y las superficies públicas expuestas.

Los verticales posteriores decidirán tooling, umbrales exactos, dashboards internos y automatización fina, pero SOBRE esta foundation.
