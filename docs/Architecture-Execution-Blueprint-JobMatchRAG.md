# Architecture & Execution Blueprint — JobMatchRAG

**Estado:** borrador de trabajo  
**Base:** derivado del PRD `docs/PRD-JobMatchRAG.md` y de las recomendaciones arquitectónicas conversadas  
**Objetivo:** consolidar en un solo documento la propuesta de arquitectura, verticales, estrategia de diseño, roadmap, changes SDD y estrategia de documentación del proyecto.

---

## 1. Resumen ejecutivo

La recomendación para JobMatchRAG es construir un **monolito modular orientado por capacidades de negocio**, no una arquitectura de microservicios.

Las razones son:

- producto **single-candidate** en V1;
- presupuesto operativo muy bajo (**5–10 €/mes**);
- infraestructura doméstica limitada y ya compartida con otros servicios;
- fuerte acoplamiento natural entre ingesta, canonicidad, scoring, publicación y alertas;
- necesidad de entregar valor real antes que complejidad operativa.

La estrategia general recomendada es:

1. modelar el sistema por **verticales de negocio**;
2. separar claramente **raw → normalized → canonical → scored → published/notified**;
3. introducir IA solo donde aporte valor real y con coste controlado;
4. usar SDD para dividir el trabajo en changes pequeños, dependientes y ejecutables.

---

## 2. Verticales de negocio recomendadas

Se identifican **8 verticales principales**.

### 2.1 Ingesta de fuentes

Responsabilidades:

- scrapers/adapters por portal;
- ejecución programada;
- trazabilidad de runs;
- captura de raw snapshots;
- detección de cambios relevantes.

### 2.2 Normalización y canonicidad

Responsabilidades:

- mapeo a oferta normalizada;
- deduplicado entre fuentes;
- creación/actualización de oferta canónica;
- resolución de empresa canónica;
- manejo de republicaciones;
- selección de URL principal.

### 2.3 Matching / Scoring

Responsabilidades:

- score por reglas;
- ajuste LLM prudente;
- clasificación `prioritaria | revisar | descartar`;
- explicación interna del resultado;
- compatibilidad geográfica y de modalidad.

### 2.4 Dashboard público

Responsabilidades:

- listado público de ofertas;
- ordenación por columnas;
- exposición de score final y estado;
- métricas públicas del sistema;
- lectura simple sin detalle interno excesivo.

### 2.5 Recruiter Chat / RAG

Responsabilidades:

- corpus documental del candidato;
- chunking e indexado;
- retrieval;
- chat recruiter-facing;
- persistencia de sesiones y mensajes;
- límites de uso y guardrails.

### 2.6 Alertas

Responsabilidades:

- detección de nuevas apariciones relevantes;
- comparación contra umbral configurable;
- envío individual a Telegram;
- registro de notificaciones enviadas.

### 2.7 Administración / Operación

Responsabilidades:

- lanzar scrapers;
- reindexar corpus;
- modificar pesos;
- modificar umbral;
- operar el sistema sin exponer controles al público.

### 2.8 Observabilidad y control de coste

Responsabilidades:

- salud de scrapers;
- métricas de actividad;
- control de gasto del chatbot/LLM;
- política de degradación;
- visibilidad operativa mínima.

---

## 3. Capacidades transversales

Estas piezas no son verticales de negocio, sino soporte transversal:

- configuración;
- autenticación/autorización del admin;
- logging;
- rate limiting;
- integración con LLM y embeddings mediante puertos/adapters;
- acceso a base de datos y migraciones;
- scheduler y ejecución de jobs.

Estas capacidades deben vivir en `shared/` o `platform/`, sin absorber la lógica de negocio.

---

## 4. Estilo arquitectónico recomendado

## 4.1 Principio general

**Monolito modular con límites claros entre verticales.**

### Por qué NO microservicios en V1

- aumentarían coste operativo;
- complicarían despliegue, trazabilidad y debugging;
- introducirían coordinación extra innecesaria;
- no hay múltiples equipos independientes ni necesidades de escalado organizativo que lo justifiquen.

### Beneficios del monolito modular

- una sola base de código;
- una sola base de datos de sistema;
- menos moving parts;
- mejor velocidad de entrega;
- posibilidad de evolucionar más adelante si un módulo lo pide de verdad.

---

## 5. Organización recomendada del código

La organización recomendada es **por capacidad de negocio**, no por tipo técnico.

### 5.1 Lo que NO se recomienda

Evitar estructuras del tipo:

- `controllers/`
- `services/`
- `repositories/`
- `models/`

como raíz principal del proyecto.

### 5.2 Lo que SÍ se recomienda

Ejemplo conceptual:

```text
src/
  job_ingestion/
  offer_canonization/
  offer_scoring/
  public_dashboard/
  recruiter_chat/
  notifications/
  admin_panel/
  shared/
```

Dentro de cada vertical, dos niveles posibles:

### Opción A — Simple al inicio

```text
vertical/
  entities.py
  use_cases.py
  repository.py
  api.py
  models.py
```

### Opción B — Más formal si el módulo crece

```text
vertical/
  domain/
  application/
  infrastructure/
  contracts/
```

La recomendación es arrancar simple, pero respetando boundaries desde el primer día.

---

## 6. Modelo conceptual del sistema

### 6.1 Entidades principales

Partiendo del PRD, el núcleo conceptual gira alrededor de:

- `Candidate`
- `Source`
- `SourceRun`
- `RawOffer`
- `NormalizedOffer`
- `CanonicalOffer`
- `OfferSource`
- `Company`
- `OfferScore`
- `OfferStatus`
- `CandidateDocument`
- `CandidateChunk`
- `ChatSession`
- `ChatMessage`
- `TelegramNotification`

### 6.2 Regla de separación de estados de la oferta

La oferta debería vivir en capas distintas:

1. **Raw** — lo capturado tal cual;
2. **Normalized** — shape común y comparable;
3. **Canonical** — representación de producto;
4. **Scored** — enriquecida con score y estado;
5. **Published/Notified** — visible y eventualmente alertada.

Esta separación es obligatoria para:

- rehacer parsers;
- recalcular dedupe;
- depurar scoring;
- mantener trazabilidad;
- evolucionar reglas sin romper histórico.

---

## 7. Flujos principales recomendados

### 7.1 Flujo de oferta

1. ejecutar run por fuente;
2. capturar raw offers;
3. normalizar;
4. deduplicar;
5. crear/actualizar canonical offer;
6. aplicar scoring por reglas;
7. aplicar ajuste LLM si corresponde;
8. asignar estado final;
9. publicar en dashboard;
10. notificar por Telegram si nueva aparición + supera umbral.

### 7.2 Flujo de chatbot

1. recibir pregunta;
2. validar rate limit y política de uso;
3. recuperar contexto del corpus;
4. generar respuesta;
5. persistir conversación;
6. devolver respuesta.

### 7.3 Flujo de recarga del corpus

1. acción manual desde admin;
2. relectura del corpus fuente;
3. rechunking y reindexado;
4. sustitución segura del índice activo.

---

## 8. Separación pública / privada

### Público

- listado de ofertas;
- score final;
- estado;
- métricas públicas;
- chatbot recruiter-facing.

### Privado

- lanzar scrapers;
- reindexar corpus;
- tocar pesos;
- tocar umbral;
- acceder a detalles internos del scoring y operación.

Regla: la UI pública **consume proyecciones ya calculadas**. No debe contener lógica central de matching, canonicidad o scoring.

---

## 9. Eventos internos recomendados

Aunque el sistema sea monolítico, conviene modelar eventos internos conceptuales como:

- `source_run_completed`
- `raw_offer_captured`
- `normalized_offer_created`
- `canonical_offer_created`
- `canonical_offer_updated`
- `offer_scored`
- `offer_became_prioritaria`
- `telegram_alert_sent`
- `candidate_corpus_reindexed`

No se propone Kafka ni event bus complejo en V1. Alcanzaría con:

- tabla de jobs/runs;
- outbox simple si hiciera falta;
- comandos internos desacoplados por módulos.

---

## 10. Reglas arquitectónicas no negociables

1. **Separar extracción de interpretación.** Capturar no es igual a inferir.
2. **No mezclar raw con canonical.**
3. **El score debe ser auditable internamente.**
4. **Toda dependencia de LLM debe pasar por puertos/adapters reemplazables.**
5. **La IA es optativa a nivel de arquitectura, no el núcleo del sistema.**
6. **El coste es un constraint arquitectónico real.**
7. **La UI pública no decide negocio.**
8. **El admin es una superficie separada y protegida.**

---

## 11. Orientación técnica recomendada

> Esta sección es una recomendación, no una decisión cerrada.

### Backend

Dirección recomendada:

- Python;
- FastAPI como opción preferente por control y ligereza;
- SQLAlchemy + Alembic;
- PostgreSQL 16 como fuente central de verdad.

### Alternativa válida

- Django + Django Admin.

Tradeoff:

- acelera admin y piezas CRUD;
- pero exige más disciplina para no mezclar capas.

### Jobs

Dirección recomendada en V1:

- scheduler simple;
- tabla de runs/jobs;
- workers del mismo proyecto;
- sin RabbitMQ/Kafka ni topologías complejas al inicio.

### RAG

Dirección recomendada:

- PostgreSQL + `pgvector`;
- un único sistema persistente si es viable.

### Filosofía general

Resolver primero el problema de producto. Escalar la topología solo si aparece una necesidad real.

---

## 12. Estrategia SDD recomendada

No se recomienda un único mega-change “build JobMatchRAG”.

Se recomienda dividir en changes pequeños, secuenciales y con dependencias claras.

### 12.1 Estructura de artefactos por change

Cada change importante debería tener:

- `proposal.md`
- `spec.md`
- `design.md`
- `tasks.md`

### 12.2 Primer backlog de changes sugerido

| Change | Objetivo | Dependencias | Resultado esperado |
| --- | --- | --- | --- |
| `project-foundation` | Base del proyecto, estructura modular, config, DB, auth/admin mínimo, observabilidad mínima | ninguna | repositorio listo para crecer sin caos |
| `source-ingestion-framework` | framework base de fuentes, scheduler, source runs, raw offers, errores y retries | `project-foundation` | pipeline genérico de ingesta |
| `first-source-infojobs` | primer adapter real de fuente | `source-ingestion-framework` | primera fuente funcional extremo a extremo |
| `normalization-and-canonical-offers` | normalización, oferta canónica, company base, offer_sources | `first-source-infojobs` | modelo estable de oferta de producto |
| `dedupe-and-republication-rules` | dedupe entre fuentes y republicaciones | `normalization-and-canonical-offers` | consolidación correcta del histórico |
| `rule-based-scoring` | score por reglas, compatibilidad geográfica, estados | `dedupe-and-republication-rules` | matching usable sin IA |
| `llm-score-adjustment` | capa de ajuste semántico prudente y controlada | `rule-based-scoring` | mejora de matching sin perder control |
| `public-dashboard` | listado público, ordenación, métricas simples | `rule-based-scoring` | escaparate funcional visible |
| `telegram-alerts` | threshold, alertas individuales, no duplicación | `rule-based-scoring` | utilidad real para Pablo |
| `recruiter-rag-corpus` | candidate docs, chunking, exclusiones, reindex manual | `project-foundation` | base del corpus preparada |
| `recruiter-chat-experience` | chat, retrieval, límites, persistencia, guardrails | `recruiter-rag-corpus` | chatbot recruiter-facing funcional |
| `admin-operations` | lanzar scrapers, reindexar, tocar pesos y umbral | `source-ingestion-framework`, `recruiter-rag-corpus`, `rule-based-scoring` | operación privada mínima |
| `cost-control-and-degradation` | medición de gasto y degradación del chatbot | `recruiter-chat-experience`, `telegram-alerts` | control operativo del presupuesto |

---

## 13. Orden de implementación recomendado

### Fase 1 — Pipeline útil de verdad

1. `project-foundation`
2. `source-ingestion-framework`
3. `first-source-infojobs`
4. `normalization-and-canonical-offers`
5. `dedupe-and-republication-rules`
6. `rule-based-scoring`
7. `telegram-alerts`

Con esto ya existe una herramienta útil para Pablo.

### Fase 2 — Escaparate público

8. `public-dashboard`

### Fase 3 — Capa IA recruiter-facing

9. `recruiter-rag-corpus`
10. `recruiter-chat-experience`

### Fase 4 — Operación madura

11. `admin-operations`
12. `llm-score-adjustment`
13. `cost-control-and-degradation`
14. siguientes fuentes adicionales

---

## 14. Estrategia de documentación recomendada

## 14.1 Documentos base del proyecto

| Documento | Propósito | Contenido esperado |
| --- | --- | --- |
| `PRD-JobMatchRAG.md` | definición de producto | problema, objetivos, alcance, NFRs, métricas, riesgos |
| `Architecture-Execution-Blueprint-JobMatchRAG.md` | visión arquitectónica consolidada | verticales, flujos, módulos, roadmap, SDD |
| `Open-Questions-Architecture-Decisions-JobMatchRAG.md` | backlog de decisiones pendientes | huecos, preguntas abiertas, tradeoffs, prioridad |
| `architecture/data-model.md` | modelo conceptual de datos | entidades, relaciones, invariantes, raw/normalized/canonical |
| `architecture/scoring-design.md` | diseño del matching | señales, pesos, fórmula, estados, rol del LLM |
| `architecture/rag-design.md` | diseño del chatbot y corpus | corpus, chunking, retrieval, límites, guardrails |
| `operations/runbook.md` | operación diaria | lanzar scrapers, reindexar, errores, recuperación |
| `engineering/testing-strategy.md` | estrategia de calidad | tests por capa, contratos, fixtures, smoke tests |
| `operations/security-abuse.md` | seguridad y abuso | rate limit, prompt injection, admin, exposición pública |
| `operations/observability-costs.md` | control técnico y económico | métricas, presupuesto, degradación, alertas |

## 14.2 ADRs iniciales sugeridos

| ADR | Decisión |
| --- | --- |
| `ADR-001` | monolito modular por verticales |
| `ADR-002` | base de datos principal y estrategia vectorial |
| `ADR-003` | modelo de jobs/scheduler |
| `ADR-004` | estrategia de scoring híbrido |
| `ADR-005` | política de degradación por coste |

## 14.3 Artefactos SDD por change

Por cada change importante:

- `proposal.md`: por qué existe el cambio;
- `spec.md`: qué debe cumplirse;
- `design.md`: cómo se resuelve técnicamente;
- `tasks.md`: desglose implementable.

---

## 15. Mapa de documentación con tres columnas

### 15.1 Documentos ya rellenables

| Ya rellenables | Parcialmente rellenables | Bloqueados por decisiones |
| --- | --- | --- |
| PRD | scoring design | ADRs tecnológicas finales |
| architecture overview | RAG design | deployment design detallado |
| bounded contexts / module map | testing strategy | schema físico definitivo |
| data model conceptual | security-abuse | contratos API exactos |
| NFRs / constraints | observability-costs | stack final cerrada |
| risk register inicial | runbook detallado | modelo exacto de autenticación admin |
| roadmap de cambios | admin UI flows | política final de retención y privacidad |
| operation overview | public UX detail | thresholds exactos de scoring y alertas |

### 15.2 Lectura del mapa

#### Ya rellenables

Se pueden escribir hoy sin inventar demasiado, porque el PRD ya define suficiente contexto.

#### Parcialmente rellenables

Se pueden arrancar, pero requieren dejar secciones marcadas como pendientes de cerrar.

#### Bloqueados por decisiones

No conviene cerrarlos todavía porque dependen de elecciones técnicas u operativas aún no resueltas.

---

## 16. Qué NO hacer

- no introducir microservicios en V1;
- no construir un dashboard público complejo antes de tener pipeline útil;
- no basar todo el matching en LLM;
- no mezclar scraper, normalización y scoring en el mismo bloque de lógica;
- no modelar el proyecto por carpetas genéricas tipo `services/` y `controllers/`;
- no sobrediseñar para multi-candidate en la primera iteración;
- no gastar presupuesto en infraestructura innecesaria antes de validar utilidad.

---

## 17. Recomendación final

La secuencia arquitectónica correcta para JobMatchRAG es:

1. **pipeline útil**;
2. **canonización estable**;
3. **matching auditable**;
4. **alertas reales**;
5. **dashboard público**;
6. **chatbot recruiter-facing**;
7. **operación, seguridad y control de coste**.

Primero valor. Después escaparate. Después sofisticación.
