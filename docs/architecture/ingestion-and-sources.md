# Ingestion & Sources — JobMatchRAG

## 1. Purpose

Este documento fija la foundation de ingesta: qué es una fuente válida, cómo corre un run, qué contrato común deben respetar los adapters y cómo se incorporan nuevas fuentes sin romper la trazabilidad del pipeline.

No define implementación runtime ni estrategia concreta por portal. Define GOVERNANCE, que es otra cosa.

## 2. Source Governance Baseline

### 2.1 First production source

La primera fuente de producción aceptada para V1 es **InfoJobs official API**.

- se usa como referencia inicial para cerrar el contrato de fuente;
- no autoriza a acoplar el sistema a particularidades irrepetibles de InfoJobs;
- futuras fuentes deben entrar bajo el mismo modelo de run, snapshots, normalización y errores.

### 2.2 Source registry intent

Cada fuente soportada debe existir como una entrada explícita del sistema, con al menos:

| Field | Intent |
|---|---|
| `source_key` | identificador estable de la fuente |
| `display_name` | nombre legible para operación/auditoría |
| `status` | habilitada, pausada o retirada |
| `priority` | preferencia operativa o de source-of-truth |
| `capabilities` | filtros disponibles, límites, modalidad de captura |
| `policy_notes` | restricciones legales u operativas conocidas |

El registry existe para gobernar fuentes como productos operables, no como scripts sueltos.

## 3. Canonical Ingestion Flow

La ingesta respeta la secuencia global del sistema:

`source -> raw -> normalized -> canonical -> eligibility -> scored -> published/notified`

Dentro de esa secuencia, la responsabilidad propia de ingesta cubre:

1. seleccionar la fuente y abrir contexto de run;
2. ejecutar captura bajo el adapter correspondiente;
3. persistir `RawOfferSnapshot` sin reinterpretación destructiva;
4. entregar material trazable a normalización.

La ingesta puede reducir ruido temprano, pero NO decide la elegibilidad final del producto.

## 4. Shared source-ingestion framework boundary

`source-ingestion-framework` fija un framework común adapter-agnostic. Su scope es SOLO:

- contrato compartido de `SourceAdapter`;
- ejecución `job -> run`;
- trazabilidad estructurada por run;
- taxonomía de errores + retries selectivos;
- guardrails por defecto de retries, alcance y rate-limit awareness.

Quedan fuera de este framework:

- adapters concretos como InfoJobs;
- normalización/canonicalización;
- eligibility/scoring;
- workflows admin concretos o thresholds operativos finos.

## 5. SourceAdapter Contract

Toda fuente futura debe respetar un contrato común equivalente a:

```text
SourceAdapter
- source_key
- capabilities: {pagination, time_windows, supported_filters, checkpoints, rate_limit}
- fetch(run_context) -> FetchOutcome(raw_items, checkpoint_hint, rate_limit_observations)
- classify_error(error) -> ErrorClassification(category, retryable)
```

### Contract rules

- `fetch(run_context)` obtiene resultados bajo contexto explícito de run;
- `capabilities` declara qué optimizaciones source-side existen sin volverlas autoridad canónica;
- `classify_error(error)` traduce fallos de fuente a clases operables comunes;
- el framework consume snapshots raw y metadata operativa, pero NO absorbe normalización ni scoring;
- el adapter encapsula rarezas de la fuente, pero no redefine el dominio;
- la salida debe poder seguir auditándose hasta el `RawOfferSnapshot` original.

## 6. Job and run traceability model

La ejecución se modela como `job + run`.

### 6.1 Job intent

`IngestionJob` describe intención reusable:

- fuente objetivo;
- filter intent pedido por operación;
- ventana temporal pedida, si aplica;
- límites máximos del run (retries, fetch scope, item scope);
- actor o trigger que pidió la ejecución.

### 6.2 Run execution record

Cada ejecución concreta crea un `RunRecord` / `IngestionRun` independiente del job padre.

Debe capturar como mínimo:

- `job_id` y `run_id`;
- `source_key`;
- snapshot de capacidades del adapter usado;
- snapshot del filter intent;
- timestamps de inicio/fin;
- counters de fetch/items;
- `checkpoint_in` / `checkpoint_out`;
- `retry_count` + historial de retries;
- `rate_limit_observations`;
- `error_summary` categorizado;
- estado final y motivo de cierre.

Esto permite correr el mismo job múltiples veces sin mezclar intent reusable con intentos reales.

## 7. Run Traceability Model

Cada ejecución de fuente debe crear un `RunRecord` trazable.

### 7.1 Minimum run expectations

Un run debe permitir responder, como mínimo:

- qué fuente se ejecutó;
- cuándo empezó y terminó;
- con qué estado final cerró;
- cuántos items se capturaron;
- qué capacidades declaró el adapter para ese run;
- qué filtros source-side se intentaron usar;
- qué checkpoints entraron/salieron;
- qué errores ocurrieron;
- si hubo retry, partial closure o corte terminal.

### 7.2 Run status intent

Sin fijar schema físico todavía, el modelo de run debe distinguir al menos:

| Status intent | Meaning |
|---|---|
| `started` | ejecución abierta |
| `completed` | ejecución terminada con resultado usable |
| `partial` | ejecución con material recuperado pero incidencias |
| `failed` | ejecución cerrada sin resultado usable |

El objetivo no es tener nombres mágicos hoy, sino una semántica operable y auditable.

Runs `partial` existen para reflejar degradación real: hubo material usable, pero el run cerró bajo límites operativos, retries agotados o presión de rate limit.

## 8. Error classes, retries, and guardrails baseline

Los errores de fuente se clasifican en dos grupos operativos:

| Class | Meaning | Expected treatment |
|---|---|---|
| `retryable` | fallos temporales o recuperables | pueden reintentarse bajo política controlada |
| `terminal` | fallos no recuperables para ese run | cortan o cierran el run sin insistir ciegamente |

### Retry principles

- retry no significa loop infinito;
- la clasificación vive detrás del adapter, pero la semántica es común;
- el framework reintenta SOLO errores marcados como `retryable`;
- el run debe conservar evidencia del error, incluso si luego recupera;
- la operación debe poder distinguir “fuente caída” de “dato incompatible”.

### Guardrails por defecto

El framework común debe aplicar guardrails sin depender de thresholds por proveedor:

- retries acotados;
- alcance acotado por run (fetch calls/items);
- cierre explícito `partial` cuando se recupera material usable pero el run queda degradado;
- ejecución rate-limit-aware con observaciones estructuradas del límite encontrado.

No se fijan todavía backoff exacto ni límites numéricos: eso pertenece a verticales posteriores.

## 9. Filtering Authority

El sistema PUEDE usar filtros del lado de la fuente para reducir ruido, coste y volumen inicial.

Pero la autoridad final sigue siendo interna:

- los filtros del portal NO reemplazan `eligibility`;
- una oferta que escapó al filtrado externo todavía debe pasar filtros duros propios;
- scoring solo arranca después de la validación interna.

Esto evita que el criterio de producto quede secuestrado por capacidades o sesgos del portal.

## 10. InfoJobs-First Onboarding Policy

InfoJobs entra primero porque destraba V1 con una fuente oficial y relativamente limpia, no porque vaya a ser la única verdad para siempre.

### Onboarding rules for future sources

Una nueva fuente solo debería entrar cuando pueda aportar:

1. un `SourceAdapter` bajo contrato común;
2. trazabilidad de runs y errores equivalente a la fuente inicial;
3. snapshots raw preservados;
4. normalización compatible con el shape común;
5. notas de riesgo legal/operativo explícitas.

Si una fuente exige hacks que rompen el contrato, el problema NO es “la documentación”: el problema es que la fuente todavía no está lista para foundation.

## 11. Boundaries for Future Vertical Changes

Los próximos changes verticales deben reutilizar estas reglas:

- la fuente inicial es InfoJobs official API;
- el registry de fuentes es explícito;
- todo adapter entra por contrato común;
- el framework común gobierna `job -> run`, errores, retries y guardrails antes de cualquier adapter concreto;
- todo run deja trazabilidad y clasificación de errores;
- los filtros de fuente ayudan, pero no sustituyen elegibilidad interna.

Este documento fija gobierno y límites. La implementación concreta del framework común ya queda cerrada en `source-ingestion-framework`; los adapters concretos siguen para verticales derivadas.
