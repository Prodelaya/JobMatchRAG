# Ingesta y fuentes — JobMatchRAG

## 1. Propósito

Este documento fija la foundation de ingesta: qué es una fuente válida, cómo corre un run, qué contrato común deben respetar los adapters y cómo se incorporan nuevas fuentes sin romper la trazabilidad del pipeline.

No define implementación runtime ni estrategia concreta por portal. Define GOVERNANCE, que es otra cosa.

## 2. Base mínima de gobernanza de fuentes

### 2.1 Primera fuente de producción

La primera fuente de producción aceptada para V1 es **InfoJobs official API**.

- se usa como referencia inicial para cerrar el contrato de fuente;
- no autoriza a acoplar el sistema a particularidades irrepetibles de InfoJobs;
- futuras fuentes deben entrar bajo el mismo modelo de run, snapshots, normalización y errores.

### 2.2 Intención del registro de fuentes

Cada fuente soportada debe existir como una entrada explícita del sistema, con al menos:

| Campo | Intención |
|---|---|
| `source_key` | identificador estable de la fuente |
| `display_name` | nombre legible para operación/auditoría |
| `status` | habilitada, pausada o retirada |
| `priority` | preferencia operativa o de fuente de verdad |
| `capabilities` | filtros disponibles, límites, modalidad de captura |
| `policy_notes` | restricciones legales u operativas conocidas |

El registry existe para gobernar fuentes como productos operables, no como scripts sueltos.

## 3. Flujo canónico de ingesta

La ingesta respeta la secuencia global del sistema:

`source -> raw -> normalized -> canonical -> eligibility -> scored -> published/notified`

Dentro de esa secuencia, la responsabilidad propia de ingesta cubre:

1. seleccionar la fuente y abrir el contexto de run;
2. ejecutar la captura bajo el adapter correspondiente;
3. derivar parámetros de proveedor desde una `capture profile` canónica sin convertirlos en autoridad semántica;
4. aplicar filtros canónicos post-fetch cuando la fuente no soporte o no pruebe la semántica requerida;
5. entregar material raw trazable para persistencia downstream sin reinterpretación destructiva.

La ingesta puede reducir ruido temprano, pero NO decide la elegibilidad final del producto. Sí debe ejecutar exclusiones canónicas explícitas y preservación de ambigüedad antes de handoff a normalización/scoring.

## 4. Boundary compartido del framework `source-ingestion`

`source-ingestion-framework` fija un framework común agnóstico al adapter. Su alcance es SOLO:

- contrato compartido de `SourceAdapter`;
- ejecución `job -> run`;
- trazabilidad estructurada por run;
- taxonomía de errores + retries selectivos;
- guardrails por defecto para retries, alcance y rate-limit awareness;
- handoff raw trazable hacia la futura persistencia de `RawOfferSnapshot`.
- `capture profile` canónica agnóstica a proveedor con familias bilingües, filtros objetivo y reglas de degradación.
- split auditable entre pushdown soportado por proveedor y filtros post-fetch internos.
- capa explícita de mapping por proveedor donde la semántica sigue siendo canónica y los params del portal son solo artefactos de ejecución.

Quedan fuera de este framework:

- adapters concretos como InfoJobs;
- normalización/canonicalización;
- eligibility/scoring;
- workflows admin concretos o umbrales operativos finos.

## 5. Contrato de `SourceAdapter`

Toda fuente futura debe respetar un contrato común equivalente a:

```text
SourceAdapter
- source_key
- capabilities: {pagination, time_windows, supported_filters, checkpoint_support, rate_limit_support}
- fetch(run_context) -> FetchOutcome(raw_items, next_checkpoint, exhausted, rate_limit_observations, error_summary)
- classify_error(error) -> ErrorClassification(category, retryable)
```

### Reglas del contrato

- `fetch(run_context)` obtiene resultados bajo un contexto explícito de run;
- `capabilities` declara qué optimizaciones del lado de la fuente existen sin volverlas autoridad canónica;
- `checkpoint_support` y `next_checkpoint` describen continuidad incremental sin imponer un schema físico de storage; si una fuente solo soporta continuidad best-effort por orden mutable del lado del proveedor, esa limitación debe quedar explícita en su contrato/documentación;
- `error_summary` permite que el adapter devuelva material raw ya preservado y un error clasificado dentro del mismo `FetchOutcome`; si ese error es `retryable`, el framework debe seguir respetando el presupuesto de retries sin descartar items ya forwardeados ni checkpoints ya avanzados;
- `rate_limit_support` declara si la fuente expone señales explícitas de cuota o solo observación pasiva;
- `classify_error(error)` traduce fallos de la fuente a clases operables comunes;
- el framework entrega payload raw y metadata operativa, pero NO implementa todavía la persistencia de `RawOfferSnapshot` dentro de este módulo compartido;
- el adapter encapsula rarezas de la fuente, pero no redefine el dominio;
- la salida debe poder seguir auditándose hasta el payload raw original y, cuando exista la etapa `raw`, hasta su `RawOfferSnapshot` persistido.

### Notas concretas de InfoJobs para la primera fuente

- `GET /offer` es la vía primaria de discovery;
- `GET /offer/{offerId}` se usa solo para enriquecer ofertas nuevas para el sistema;
- antes del adapter existe un mapper explícito `capture profile` canónica -> `InfoJobsExecutionPlan`; discovery serializa únicamente los `provider_params` aprobados por ese plan y nunca reconstruye semántica desde el request final;
- `sinceDate` y demás filtros del lado de la fuente son optimizaciones declaradas por `capabilities`, no autoridad canónica de continuidad o elegibilidad; en el InfoJobs actual eso vive como params derivados desde la `capture profile`, no en una traducción automática de `requested_window_start/end`;
- el checkpoint que vuelve del adapter representa continuación interna de página/oferta y puede convivir con el `checkpoint_in` opaco del framework sin reinterpretarlo, pero en InfoJobs la garantía real es solo best-effort porque el proveedor no documenta orden estable entre llamadas; el payload debe incluir marcador de adapter/versión para rechazar checkpoints ajenos o incompatibles de forma explícita;
- el handoff raw preserva capturas hermanas `list` y `detail` cuando existe detalle, y si el detalle de una oferta nueva queda bloqueado por presupuesto/rate limit igual preserva el raw `list` con una marca explícita de `detail` diferido.
- reglas semánticas como modalidad/geografía AVE-friendly o detección de consultoría/body-shopping permanecen post-fetch dentro de JobMatchRAG aunque InfoJobs provea filtros parciales.
- cada proyección a InfoJobs queda auditada con `authority=canonical`, `trust_level` y `rationale`; `experienceMin` es partial-but-strong, `category/subcategory` son contextuales, `teleworking` es support-only y `sinceDate` es optimization-only.

## 6. Modelo de trazabilidad de `job` y `run`

La ejecución se modela como `job + run`.

### 6.1 Intención de `job`

`IngestionJob` describe una intención reusable:

- fuente objetivo;
- filter intent pedido por operación;
- ventana temporal pedida, si aplica;
- límites máximos del run (retries, fetch scope, item scope);
- actor o trigger que pidió la ejecución.

### 6.2 Registro de ejecución de `run`

Cada ejecución concreta crea un `RunRecord` / `IngestionRun` independiente del job padre.

Debe capturar como mínimo:

- `job_id` y `run_id`;
- `source_key`;
- snapshot de capabilities del adapter usado;
- snapshot del filter intent;
- traza canónica con `capture profile`, plan de ejecución por proveedor (`family_plans`, proyecciones, degradaciones, checks pendientes), params derivados, identidades canónicas de filtros pusheados, mapping explícito semántica→param de proveedor, request efectivo por query con identidad de plan (`family_key` / idioma / `query_label`), deduplicación por `source_offer_id` a nivel run y versiones de datasets curados consultados;
- timestamps de inicio/fin;
- counters de fetch/items;
- `checkpoint_in` / `checkpoint_out`;
- `retry_count` + historial de retries;
- `rate_limit_observations`;
- `error_summary` categorizado;
- estado final y motivo de cierre.

Esto permite correr el mismo job múltiples veces sin mezclar la intención reusable con los intentos reales.

## 7. Modelo de trazabilidad de runs

Cada ejecución de fuente debe crear un `RunRecord` trazable.

### 7.1 Expectativas mínimas de run

Un run debe permitir responder, como mínimo:

- qué fuente se ejecutó;
- cuándo empezó y terminó;
- con qué estado final cerró;
- cuántos items se capturaron;
- qué capabilities declaró el adapter para ese run;
- qué filtros del lado de la fuente se intentaron usar;
- qué parte del criterio canónico se intentó empujar al proveedor y qué parte quedó post-fetch;
- qué datasets curados participaron (por ejemplo ciudades híbridas AVE-friendly y lista provisional de consultoras conocidas) y con qué versión;
- qué checkpoints entraron/salieron;
- qué queries concretas se emitieron aunque no hayan forwardeado ofertas (por ejemplo query vacía, totalmente excluida o deduplicada downstream);
- qué errores ocurrieron;
- si hubo retry, cierre parcial o corte terminal.

### 7.2 Intención de estados de run

Sin fijar todavía un schema físico, el modelo de run debe distinguir al menos:

| Estado | Significado |
|---|---|
| `pending` | run creado pero todavía sin ejecutarse |
| `running` | ejecución abierta |
| `completed` | ejecución terminada con resultado usable |
| `partial` | ejecución con material recuperado pero con incidencias |
| `failed` | ejecución cerrada sin resultado usable |

El vocabulario activo del framework usa exactamente `pending`, `running`, `completed`, `partial` y `failed`. El objetivo no es inventar nombres mágicos, sino mantener una semántica operable y auditable coherente entre documentación e implementación.

Los runs `partial` existen para reflejar degradación real: hubo material usable, pero el run cerró bajo límites operativos, retries agotados o presión de rate limit.

## 8. Base mínima de clases de error, retries y guardrails

Los errores de fuente se clasifican en dos grupos operativos:

| Clase | Significado | Tratamiento esperado |
|---|---|---|
| `retryable` | fallos temporales o recuperables | pueden reintentarse bajo una política controlada |
| `terminal` | fallos no recuperables para ese run | cortan o cierran el run sin insistir a ciegas |

### Principios de retry

- retry no significa loop infinito;
- la clasificación vive detrás del adapter, pero la semántica es común;
- el framework reintenta SOLO errores marcados como `retryable`;
- el run debe conservar evidencia del error, incluso si luego se recupera;
- la operación debe poder distinguir “fuente caída” de “dato incompatible”.

### Guardrails por defecto

El framework común debe aplicar guardrails sin depender de umbrales por proveedor:

- retries acotados;
- alcance acotado por run (fetch calls/items);
- cierre explícito `partial` cuando se recupera material usable pero el run queda degradado;
- ejecución rate-limit-aware con observaciones estructuradas del límite encontrado.

Todavía no se fijan el backoff exacto ni los límites numéricos: eso pertenece a verticales posteriores.

## 9. Autoridad del filtrado

El sistema PUEDE usar filtros del lado de la fuente para reducir ruido, coste y volumen inicial.

Pero la autoridad final sigue siendo interna:

- los filtros del portal NO reemplazan `eligibility`;
- una oferta que escapó al filtrado externo igualmente debe pasar filtros duros propios;
- el scoring solo arranca después de la validación interna.

Esto evita que el criterio de producto quede secuestrado por capacidades o sesgos del portal.

## 10. Política de onboarding InfoJobs-first

InfoJobs entra primero porque destraba V1 con una fuente oficial y relativamente limpia, no porque vaya a ser la única verdad para siempre.

### Reglas de onboarding para fuentes futuras

Una nueva fuente solo debería entrar cuando pueda aportar:

1. un `SourceAdapter` bajo contrato común;
2. trazabilidad de runs y errores equivalente a la fuente inicial;
3. snapshots raw preservados;
4. normalización compatible con la forma común;
5. notas explícitas de riesgo legal/operativo.

Si una fuente exige hacks que rompen el contrato, el problema NO es “la documentación”: el problema es que la fuente todavía no está lista para foundation.

## 11. Boundaries para cambios verticales futuros

Los próximos changes verticales deben reutilizar estas reglas:

- la fuente inicial es InfoJobs official API;
- el registry de fuentes es explícito;
- todo adapter entra por contrato común;
- el framework común gobierna `job -> run`, errores, retries y guardrails antes de cualquier adapter concreto;
- todo run deja trazabilidad y clasificación de errores;
- los filtros de fuente ayudan, pero no sustituyen la elegibilidad interna.

Este documento fija gobierno y límites. La implementación concreta del framework común ya queda cerrada en `source-ingestion-framework`; los adapters concretos siguen para verticales derivadas.
