# Domain & Data Overview — JobMatchRAG

## 1. Purpose

Este documento define las entidades y transiciones del dominio base de JobMatchRAG. La idea es SIMPLE: separar estados del pipeline para poder auditar, recalcular y evolucionar reglas sin romper histórico.

## 2. Core Domain Objects

| Domain object | Role in the system |
|---|---|
| `Source` | Registro de una fuente soportada bajo contrato común |
| `RunRecord` | Trazabilidad de una ejecución por fuente/acción |
| `RawOfferSnapshot` | Captura original sin reinterpretación |
| `NormalizedOffer` | Oferta mapeada a shape común comparable |
| `CanonicalOffer` | Representación de producto consolidada |
| `OfferEvidence` | Evidencia por fuente que respalda la oferta canónica |
| `EligibilityDecision` | Resultado de filtros duros y motivos |
| `ScoreBreakdown` | Resultado auditable de scoring por reglas |
| `LLMAdjustment` | Delta acotado y explicado sobre score base |
| `PublishedOfferProjection` | Vista calculada para dashboard público |
| `TelegramNotification` | Registro de alerta enviada por nueva oportunidad |

## 3. Lifecycle by Stage

El pipeline del dominio sigue esta secuencia:

`source -> raw -> normalized -> canonical -> eligibility -> scored -> published/notified`

### 3.1 `source`

Una fuente se ejecuta bajo un `RunRecord` gobernado por el framework común `job -> run`. Ese run tiene contexto, timestamps, estado, counters, checkpoints, snapshot de capabilities/filter intent y errores clasificados.

### 3.2 `raw`

Cada captura queda como `RawOfferSnapshot`, preservando el material original para debugging, replay y comparación histórica.

### 3.3 `normalized`

El snapshot se transforma en `NormalizedOffer`, que ya expresa campos comunes como título, empresa, ubicación, modalidad, salario, descripción, URL y metadatos de captura, con calidad suficiente para comparar entre fuentes.

### 3.4 `canonical`

Las normalizadas equivalentes se consolidan en una sola `CanonicalOffer`, acompañada por `OfferEvidence[]` para no perder el origen ni la trazabilidad de cada señal.

### 3.5 `eligibility`

Sobre la oferta canónica corren filtros duros. Si falla, el sistema conserva la decisión y sus razones; si pasa, habilita scoring.

### 3.6 `scored`

La oferta elegible recibe un `ScoreBreakdown` por reglas y, si corresponde, un `LLMAdjustment` limitado. El resultado final determina score y estado operativo.

### 3.7 `published/notified`

La publicación genera una `PublishedOfferProjection` para el dashboard. Si además la oportunidad es nueva y su score final es >= 70, se registra `TelegramNotification`.

## 4. Evidence Model

La evidencia es el puente entre captura y producto. `OfferEvidence` debe permitir responder, como mínimo:

- de qué fuente vino una señal;
- qué snapshot la respaldó;
- qué campos fueron consistentes entre fuentes;
- qué campo ganó como source of truth;
- con qué confianza se consolidó una empresa u oferta.

La oferta canónica NUNCA debe borrar la diversidad de evidencia original. Consolida, no aplasta historia.

## 5. Canonicalization Rules

### 5.1 Canonical offer

Si varias fuentes describen el mismo trabajo activo, el sistema mantiene **una sola** `CanonicalOffer` con múltiples evidencias enlazadas.

### 5.2 Source-of-truth preference

Los campos de la canónica se resuelven con una preferencia definida por fuente, pero con overrides por campo cuando otra evidencia es claramente mejor.

### 5.3 Canonical company

La resolución de empresa debe ser cautelosa y confidence-aware. Si la evidencia no alcanza para unificar sin riesgo, se prefiere no consolidar agresivamente.

## 6. Republication Boundary

Actualizar una oferta existente y detectar una nueva oportunidad NO son lo mismo.

- si la similitud y continuidad indican el mismo aviso activo, se actualiza evidencia/histórico;
- si hay gap temporal y similitud suficiente para inferir republicación, se crea una **nueva oportunidad**;
- la republicación no debe destruir la relación con el histórico previo, pero sí habilitar una nueva publicación/notificación.

## 7. Publication and History Model

- el histórico completo vive en las capas internas del pipeline;
- la superficie pública consume una proyección calculada, no las tablas/objetos crudos del dominio;
- una oferta descartada por elegibilidad puede seguir siendo parte del histórico interno aunque no se publique;
- las notificaciones dependen de novedad + score, no solo de existencia.

## 8. Source execution traceability model

El dominio de ingesta necesita distinguir intención reusable de intento ejecutado:

| Object | Intent |
|---|---|
| `IngestionJob` | intención reusable para correr una fuente con cierto filter intent, ventana temporal y guardrails máximos |
| `RunRecord` / `IngestionRun` | intento concreto con status, counters, checkpoints, retries, rate-limit observations y outcome |

### 8.1 Run closure semantics

- `completed`: el run agotó su trabajo esperado y dejó material usable sin degradación operativa relevante;
- `partial`: el run dejó material usable, pero cerró degradado por límites operativos, retries agotados o rate limit;
- `failed`: el run cerró sin material usable o con error terminal que impidió handoff válido.

### 8.2 Traceability fields that must survive

El record operativo debe preservar, como mínimo:

- `job_id`, `run_id`, `source_key`;
- snapshot de capacidades declaradas por el adapter;
- snapshot de filtros source-side intentados;
- `checkpoint_in` / `checkpoint_out`;
- counters de fetch/items capturados;
- retries intentados + clasificación final del error;
- observaciones de rate limit y estado final.

## 9. Future `candidate_id` Boundary

V1 sigue siendo **single-candidate**. Aun así, la foundation deja clara la frontera para un futuro `candidate_id`:

- puede incorporarse como boundary de partición lógica en entidades de producto y corpus;
- no habilita ahora multi-candidate real, permisos por candidato ni UX multi-tenant;
- se documenta para no contaminar el dominio con supuestos imposibles de separar después.

En otras palabras: se deja la junta de dilatación, pero NO se construye el edificio de al lado todavía.

## 10. What Vertical Changes Must Respect

Todo change futuro debe respetar estas reglas:

- no mezclar `raw`, `normalized`, `canonical`, `eligibility`, `scored` y `published` en un solo estado opaco;
- no perder evidencia por fuente al consolidar;
- no mezclar la semántica `job` reusable con `run` ejecutado;
- no confundir actualización normal con republicación;
- no introducir multi-candidate real dentro de este change foundation.
