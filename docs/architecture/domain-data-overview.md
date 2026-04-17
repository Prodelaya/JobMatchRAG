# Visión general del dominio y los datos — JobMatchRAG

## 1. Propósito

Este documento define las entidades y transiciones del dominio base de JobMatchRAG. La idea es SIMPLE: separar estados del pipeline para poder auditar, recalcular y evolucionar reglas sin romper el histórico.

## 2. Objetos core del dominio

| Objeto de dominio | Rol en el sistema |
|---|---|
| `Source` | Registro de una fuente soportada bajo contrato común |
| `RunRecord` | Trazabilidad de una ejecución por fuente/acción |
| `RawOfferSnapshot` | Captura original sin reinterpretación |
| `NormalizedOffer` | Oferta mapeada a una forma común comparable |
| `CanonicalOffer` | Representación de producto consolidada |
| `OfferEvidence` | Evidencia por fuente que respalda la oferta canónica |
| `EligibilityDecision` | Resultado de filtros duros y motivos |
| `ScoreBreakdown` | Resultado auditable del scoring por reglas |
| `LLMAdjustment` | Delta acotado y explicado sobre el score base |
| `PublishedOfferProjection` | Vista calculada para el dashboard público |
| `TelegramNotification` | Registro de alerta enviada por nueva oportunidad |

## 3. Lifecycle por etapa

El pipeline del dominio sigue esta secuencia:

`source -> raw -> normalized -> canonical -> eligibility -> scored -> published/notified`

### 3.1 `source`

Una fuente se ejecuta bajo un `RunRecord` gobernado por el framework común `job -> run`. Ese run tiene contexto, timestamps, estado, counters, checkpoints, snapshot de capabilities/filter intent, errores clasificados y una traza canónica separada del request derivado al proveedor. Esa traza guarda además cada query emitida con su identidad de plan canónico (`family_key`, idioma, `query_label`), el request efectivo, los `source_offer_id` vistos/forwardeados y las deduplicaciones por run.

### 3.2 `raw`

Cada captura queda como `RawOfferSnapshot`, preservando el material original para debugging, replay y comparación histórica.

Para `first-source-infojobs`, una oferta descubierta siempre conserva el payload de listado y, cuando hubo enriquecimiento para una oferta nueva, agrega además un payload de detalle separado. Si el detalle no pudo capturarse por rate limit o presupuesto operativo, la oferta igual sobrevive con su captura `list` y una marca explícita de `detail` diferido. La regla es CLARA: `list` y `detail` son orígenes hermanos con trazabilidad propia, no una fusión destructiva.

### 3.3 `normalized`

El snapshot se transforma en `NormalizedOffer`, que ya expresa campos comunes como título, empresa, ubicación, modalidad, salario, descripción, URL y metadatos de captura, con calidad suficiente para comparar entre fuentes.

### 3.4 `canonical`

Las normalizadas equivalentes se consolidan en una sola `CanonicalOffer`, acompañada por `OfferEvidence[]` para no perder el origen ni la trazabilidad de cada señal.

### 3.5 `eligibility`

Sobre la oferta canónica corren filtros duros. Si falla, el sistema conserva la decisión y sus razones; si pasa o queda ambigua, habilita el downstream correspondiente sin perder evidencia del filtro.

### 3.6 `scored`

La oferta elegible recibe un `ScoreBreakdown` por reglas y, si corresponde, un `LLMAdjustment` limitado. El resultado final determina el score y el estado operativo.

### 3.7 `published/notified`

La publicación genera una `PublishedOfferProjection` para el dashboard. Si además la oportunidad es nueva y su score final es >= 70, se registra `TelegramNotification`.

## 4. Modelo de evidencia

La evidencia es el puente entre captura y producto. `OfferEvidence` debe permitir responder, como mínimo:

- de qué fuente vino una señal;
- qué snapshot la respaldó;
- qué campos fueron consistentes entre fuentes;
- qué campo ganó como fuente de verdad;
- con qué confianza se consolidó una empresa u oferta.
- qué evidencia fue explícita/reliable versus curada/provisional al decidir exclusión o ambigüedad.

La oferta canónica NUNCA debe borrar la diversidad de evidencia original. Consolida, no aplasta historia.

Para `source-search-strategy`, la evidencia temprana también incluye referencias a datasets curados internos. Dos casos cerrados hoy:

- `hybrid_cities`: dataset versionado en repo, sembrado desde la lista de ciudades de abril 2026, usado solo para validar híbridos fuera de Madrid con asistencia explícita `< 3 días/mes`.
- `known_consultancies`: lista provisional curada de compañías/aliases; un match sin texto explícito NO excluye, solo deja la oferta como ambigua con evidencia trazable.

## 5. Reglas de canonicalización

### 5.1 Oferta canónica

Si varias fuentes describen el mismo trabajo activo, el sistema mantiene **una sola** `CanonicalOffer` con múltiples evidencias enlazadas.

### 5.2 Preferencia de fuente de verdad

Los campos de la canónica se resuelven con una preferencia definida por fuente, pero con overrides por campo cuando otra evidencia es claramente mejor.

### 5.3 Empresa canónica

La resolución de empresa debe ser cautelosa y consciente de la confianza. Si la evidencia no alcanza para unificar sin riesgo, se prefiere no consolidar agresivamente.

## 6. Boundary de republicación

Actualizar una oferta existente y detectar una nueva oportunidad NO son lo mismo.

- si la similitud y la continuidad indican el mismo aviso activo, se actualiza evidencia/histórico;
- si hay gap temporal y similitud suficiente para inferir republicación, se crea una **nueva oportunidad**;
- la republicación no debe destruir la relación con el histórico previo, pero sí habilitar una nueva publicación/notificación.

## 7. Modelo de publicación e histórico

- el histórico completo vive en las capas internas del pipeline;
- la superficie pública consume una proyección calculada, no las tablas/objetos crudos del dominio;
- una oferta descartada por elegibilidad puede seguir siendo parte del histórico interno aunque no se publique;
- las notificaciones dependen de novedad + score, no solo de existencia.

## 8. Modelo de trazabilidad de ejecución de fuentes

El dominio de ingesta necesita distinguir intención reusable de intento ejecutado:

| Objeto | Intención |
|---|---|
| `IngestionJob` | intención reusable para correr una fuente con cierto filter intent, ventana temporal y guardrails máximos |
| `RunRecord` / `IngestionRun` | intento concreto con status, counters, checkpoints, retries, observaciones de rate limit y outcome |

### 8.1 Semántica de cierre de run

- `completed`: el run agotó su trabajo esperado y dejó material usable sin degradación operativa relevante;
- `partial`: el run dejó material usable, pero cerró degradado por límites operativos, retries agotados o rate limit;
- `failed`: el run cerró sin material usable o con error terminal que impidió un handoff válido.

### 8.2 Campos de trazabilidad que deben sobrevivir

El record operativo debe preservar, como mínimo:

- `job_id`, `run_id`, `source_key`;
- snapshot de capabilities declaradas por el adapter;
- snapshot de filtros intentados del lado de la fuente;
- `capture profile` canónica y plan derivado de ejecución (`pushed_down_filters` vs `post_fetch_filters`);
- `checkpoint_in` / `checkpoint_out`;
- counters de fetch/items capturados;
- retries intentados + clasificación final del error;
- observaciones de rate limit y estado final.
- outcomes canónicos por oferta con `evidence_refs` y versiones de datasets consultados cuando correspondan.

Cuando un source adapter produce múltiples capturas raw para la misma oferta en un mismo run, también debe sobrevivir la procedencia de cada payload (`list` vs `detail`) junto con el request efectivo de discovery que originó la evidencia.

## 9. Boundary futuro de `candidate_id`

V1 sigue siendo **single-candidate**. Aun así, la foundation deja clara la frontera para un futuro `candidate_id`:

- puede incorporarse como boundary de partición lógica en entidades de producto y corpus;
- no habilita ahora multi-candidate real, permisos por candidato ni UX multi-tenant;
- se documenta para no contaminar el dominio con supuestos imposibles de separar después.

En otras palabras: se deja la junta de dilatación, pero NO se construye el edificio de al lado todavía.

## 10. Qué deben respetar los cambios verticales

Todo change futuro debe respetar estas reglas:

- no mezclar `raw`, `normalized`, `canonical`, `eligibility`, `scored` y `published` en un solo estado opaco;
- no perder evidencia por fuente al consolidar;
- no mezclar la semántica de `job` reusable con la de `run` ejecutado;
- no confundir actualización normal con republicación;
- no introducir multi-candidate real dentro de este change foundation.
