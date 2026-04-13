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

## 4. SourceAdapter Contract

Toda fuente futura debe respetar un contrato común equivalente a:

```text
SourceAdapter
- source_key
- fetch(run_context) -> RawOfferSnapshot[]
- normalize(raw) -> NormalizedOffer
- classify_error(error) -> retryable | terminal
```

### Contract rules

- `fetch(run_context)` obtiene resultados bajo contexto explícito de run;
- `normalize(raw)` transforma cada snapshot al shape común del sistema;
- `classify_error(error)` traduce fallos de fuente a clases operables comunes;
- el adapter encapsula rarezas de la fuente, pero no redefine el dominio;
- la salida debe poder seguir auditándose hasta el `RawOfferSnapshot` original.

## 5. Run Traceability Model

Cada ejecución de fuente debe crear un `RunRecord` trazable.

### 5.1 Minimum run expectations

Un run debe permitir responder, como mínimo:

- qué fuente se ejecutó;
- cuándo empezó y terminó;
- con qué estado final cerró;
- cuántos items se capturaron;
- qué errores ocurrieron;
- si hubo retry o corte terminal.

### 5.2 Run status intent

Sin fijar schema físico todavía, el modelo de run debe distinguir al menos:

| Status intent | Meaning |
|---|---|
| `started` | ejecución abierta |
| `completed` | ejecución terminada con resultado usable |
| `partial` | ejecución con material recuperado pero incidencias |
| `failed` | ejecución cerrada sin resultado usable |

El objetivo no es tener nombres mágicos hoy, sino una semántica operable y auditable.

## 6. Error Classes and Retry Baseline

Los errores de fuente se clasifican en dos grupos operativos:

| Class | Meaning | Expected treatment |
|---|---|---|
| `retryable` | fallos temporales o recuperables | pueden reintentarse bajo política controlada |
| `terminal` | fallos no recuperables para ese run | cortan o cierran el run sin insistir ciegamente |

### Retry principles

- retry no significa loop infinito;
- la clasificación vive detrás del adapter, pero la semántica es común;
- el run debe conservar evidencia del error, incluso si luego recupera;
- la operación debe poder distinguir “fuente caída” de “dato incompatible”.

No se fijan todavía backoff exacto ni límites numéricos: eso pertenece a verticales posteriores.

## 7. Filtering Authority

El sistema PUEDE usar filtros del lado de la fuente para reducir ruido, coste y volumen inicial.

Pero la autoridad final sigue siendo interna:

- los filtros del portal NO reemplazan `eligibility`;
- una oferta que escapó al filtrado externo todavía debe pasar filtros duros propios;
- scoring solo arranca después de la validación interna.

Esto evita que el criterio de producto quede secuestrado por capacidades o sesgos del portal.

## 8. InfoJobs-First Onboarding Policy

InfoJobs entra primero porque destraba V1 con una fuente oficial y relativamente limpia, no porque vaya a ser la única verdad para siempre.

### Onboarding rules for future sources

Una nueva fuente solo debería entrar cuando pueda aportar:

1. un `SourceAdapter` bajo contrato común;
2. trazabilidad de runs y errores equivalente a la fuente inicial;
3. snapshots raw preservados;
4. normalización compatible con el shape común;
5. notas de riesgo legal/operativo explícitas.

Si una fuente exige hacks que rompen el contrato, el problema NO es “la documentación”: el problema es que la fuente todavía no está lista para foundation.

## 9. Boundaries for Future Vertical Changes

Los próximos changes verticales deben reutilizar estas reglas:

- la fuente inicial es InfoJobs official API;
- el registry de fuentes es explícito;
- todo adapter entra por contrato común;
- todo run deja trazabilidad y clasificación de errores;
- los filtros de fuente ayudan, pero no sustituyen elegibilidad interna.

Este documento fija gobierno y límites. La implementación concreta del framework de ingesta queda para `source-ingestion-framework` y verticales derivadas.
