# Open Questions & Architecture Decisions Needed — JobMatchRAG

**Estado:** backlog de decisiones pendientes  
**Objetivo:** identificar las decisiones que un equipo experto debería cerrar antes de bajar a diseño detallado, schema físico final o implementación por lotes SDD.

---

## 1. Cómo usar este documento

Este documento no redefine el PRD. Su función es:

- señalar huecos reales de definición;
- priorizar decisiones arquitectónicas y operativas;
- evitar que se diseñe o implemente a ciegas;
- servir como input para ADRs, specs y designs posteriores.

Cada decisión incluye:

- la pregunta abierta;
- por qué importa;
- impacto en arquitectura/SDD;
- recomendación inicial;
- momento recomendado para decidirla.

---

## 2. Decisiones críticas antes de diseño fino

| ID | Decisión / pregunta abierta | Por qué importa | Impacto principal | Recomendación inicial | Decidir antes de |
| --- | --- | --- | --- | --- | --- |
| D01 | **Stack backend final**: FastAPI vs Django | condiciona estructura, admin, productividad, convenciones | foundation, admin, APIs, tests | preferencia inicial: FastAPI; Django si se prioriza admin rápido | `project-foundation` |
| D02 | **Modelo de jobs**: scheduler simple, Celery-light u otro | afecta ingesta, retries, operación y observabilidad | ingesta, alertas, reindexado | arrancar simple con scheduler + tabla de runs/jobs | `source-ingestion-framework` |
| D03 | **Estrategia concreta de scraping** por fuente | afecta robustez, mantenimiento y coste de cada adapter | ingesta | combinar HTML/parsing simple y browser automation solo donde haga falta | `first-source-infojobs` |
| D04 | **Modelo de dedupe** | evita ruido y errores de consolidación | canonicidad, histórico, scoring | usar matching por señales compuestas, no por un único campo | `normalization-and-canonical-offers` |
| D05 | **Regla exacta de republicación** | separa “misma oferta actualizada” de “nueva oportunidad” | histórico, alertas | definir ventana temporal y umbral de similitud | `dedupe-and-republication-rules` |
| D06 | **Fórmula exacta de scoring por reglas** | permite empezar con matching estable y auditable | scoring, alertas, dashboard | cerrar pesos y señales antes de meter LLM | `rule-based-scoring` |
| D07 | **Umbrales exactos** (`prioritaria`, alertas, revisar) | afecta experiencia, ruido y utilidad real | scoring, Telegram, dashboard | definir con datos y calibración inicial | `rule-based-scoring` |
| D08 | **Cuándo entra el LLM en scoring** | controla coste y consistencia | scoring, costes | no llamar LLM para todo; usarlo como segunda capa selectiva | `llm-score-adjustment` |
| D09 | **RAG stack final**: pgvector u otra alternativa | condiciona diseño del corpus e indexado | recruiter chat | preferencia inicial: PostgreSQL + pgvector | `recruiter-rag-corpus` |
| D10 | **Modelo exacto del chatbot**: tono, longitud, rejections, fallback | condiciona UX, guardrails y evaluación | recruiter chat | documentar contrato conversacional explícito | `recruiter-chat-experience` |
| D11 | **Autenticación/seguridad del admin** | define superficie de riesgo real | admin, seguridad | separarlo claramente de la UI pública con auth robusta | `project-foundation` |
| D12 | **Política de retención y privacidad** | evita guardar de más o sin criterio | chats, raw logs, observabilidad | definir plazos y nivel de anonimización | `project-foundation` |
| D13 | **Métricas y alertas operativas mínimas** | sin esto no hay operación seria | observabilidad, coste | definir set mínimo de health metrics | `project-foundation` |
| D14 | **Límites de coste por componente** | el PRD fija presupuesto duro | chatbot, scoring, scraping | asignar presupuesto parcial por módulo | `cost-control-and-degradation` |
| D15 | **Preparación multi-candidate light** | evita sobreingeniería o deuda futura | modelo de datos, modularidad | introducir `candidate_id` solo donde aporte separación real desde el día 1 | `project-foundation` |

---

## 3. Huecos por dominio

## 3.1 Producto y UX pública

### Q01. Nombre público del producto

- **Estado:** pendiente en PRD.
- **Impacto:** branding, copy pública, URL final.
- **Urgencia:** baja para arquitectura, media para escaparate.

### Q02. Ubicación exacta del chatbot en la web

- **Opciones:** solo página del producto vs elemento flotante global.
- **Impacto:** layout, rate limiting percibido, coste de uso, discoverability.
- **Urgencia:** media antes del diseño de UI pública.

### Q03. Nivel de detalle de las métricas públicas

- **Pregunta:** qué se muestra exactamente y con qué frecuencia se actualiza.
- **Impacto:** dashboard, consultas, coste y diseño visual.

---

## 3.2 Ingesta y normalización

### Q04. Contrato mínimo por fuente

Falta definir:

- cómo se identifica cada run;
- qué errores se consideran recuperables;
- qué se considera cambio relevante para evitar reingesta;
- política de retries y backoff.

### Q05. Campos obligatorios y opcionales por oferta

El PRD define mínimos, pero falta decidir:

- qué hacer si faltan salario, empresa o ubicación;
- cómo marcar calidad/fiabilidad del parseo;
- qué metadatos de captura son obligatorios siempre.

### Q06. Elección de portal principal “más fiable/limpio”

Hace falta una heurística explícita para:

- preferencia entre fuentes;
- desempates;
- casos en los que la mejor URL cambia con el tiempo.

---

## 3.3 Dedupe, canonicidad y republicaciones

### Q07. Algoritmo de dedupe

Falta concretar:

- señales principales (título, empresa, dominio, descripción, ubicación, salario, modalidad);
- ponderación de similitud;
- umbral de match;
- cuándo se crea una canonical nueva en vez de actualizar una existente.

### Q08. Regla exacta de republicación

El PRD dice “si una empresa republica la misma oferta dos semanas después, tratar como nueva oportunidad”.

Falta concretar:

- si “dos semanas” es exacto o aproximado;
- qué pasa si la oferta cambia poco;
- qué eventos reinician el contador;
- cómo interactúa esto con el dedupe entre fuentes.

### Q09. Empresa canónica

Falta decidir:

- cuándo auto-unificar;
- cuándo no arriesgar y mantener separado;
- si habrá score/confianza de consolidación;
- cómo manejar empresas con naming inestable.

---

## 3.4 Scoring y matching

### Q10. Pesos exactos de la fórmula base

El PRD fija prioridades, pero no pesos operativos.

Hace falta decidir:

- peso de uso interno;
- peso de IA aplicada;
- peso de automatización;
- peso de stack/lenguaje;
- peso de aceptación junior;
- bonus Python.

### Q11. Señales explícitas vs inferidas

Hay que traducir la intención del PRD a reglas concretas:

- qué señales se consideran explícitas;
- cuánto pueden valer las inferidas;
- cuánto puede alterar el LLM el score base;
- cómo se evita sobrepremiar inferencias débiles.

### Q12. Umbrales operativos

Hace falta cerrar:

- rango de score final;
- umbral de `prioritaria`;
- umbral de `revisar`;
- umbral de alertas Telegram.

### Q13. Explicabilidad interna

Hay que definir el contrato mínimo de auditoría del scoring:

- razones positivas;
- razones negativas;
- señales detectadas;
- ajuste LLM aplicado;
- evidencia base.

---

## 3.5 Compatibilidad geográfica y modalidad

### Q14. Interpretación operativa de “ciudad con AVE”

Hay que decidir:

- catálogo exacto o regla de referencia;
- fuente del dato;
- si esto queda hardcodeado o configurable.

### Q15. Cómo inferir frecuencia presencial

Falta definir:

- patrones textuales válidos;
- qué pasa si no está explícito;
- si ausencia de dato penaliza o solo reduce confianza.

### Q16. Cómo inferir idioma de trabajo

Falta definir:

- reglas basadas en texto de la oferta;
- dominio/ubicación como señales auxiliares;
- cómo tratar casos ambiguos.

---

## 3.6 Chatbot recruiter y RAG

### Q17. Contrato de respuesta del chatbot

Falta concretar:

- longitud máxima;
- estructura de respuesta;
- cuándo usar bullets;
- cuándo rechazar;
- cómo responder si no hay suficiente contexto.

### Q18. Política de chunking e indexado

Hay que decidir:

- tamaño de chunk;
- solapamiento;
- metadatos obligatorios;
- refresh replacement strategy;
- versionado del índice.

### Q19. Selección exacta del corpus

Aunque el PRD define fuentes, falta decidir:

- criterios de exclusión;
- qué código y tests entran;
- si todo documento público entra por defecto o requiere curación previa.

### Q20. Persistencia conversacional

Hay que decidir:

- qué metadatos guardar;
- cuánto tiempo conservar mensajes;
- anonimización;
- si se registra IP completa, hash o identificador derivado.

### Q21. Defensa ante prompt injection y abuso

Hace falta concretar:

- política de rechazo;
- detección básica vs avanzada;
- logging de intentos;
- respuesta segura por defecto.

---

## 3.7 Seguridad, privacidad y operación

### Q22. Autenticación del panel admin

Preguntas concretas:

- ¿login propio, sesión integrada en la web, basic auth reforzada u otra opción?
- ¿exposición por ruta pública protegida o acceso más restringido?
- ¿habrá MFA o no?

### Q23. Política de logs y retención

Falta definir:

- retención de raw snapshots;
- retención de source run logs;
- retención de conversaciones;
- política de borrado/limpieza.

### Q24. Backups y recuperación

No está definido todavía:

- periodicidad de backups;
- qué se respalda;
- si el índice vectorial se reconstruye o también se respalda;
- tiempo objetivo de recuperación.

### Q25. Observabilidad mínima

Se deben fijar métricas mínimas como:

- scrapers exitosos/fallidos;
- tiempo por fuente;
- ofertas nuevas por run;
- coste del chatbot;
- consultas rechazadas por rate limit;
- errores de retrieval;
- alertas Telegram enviadas/fallidas.

---

## 3.8 Coste y degradación

### Q26. Budget allocation por componente

El presupuesto global está claro, pero falta repartirlo entre:

- scoring LLM;
- recruiter chat;
- embeddings/reindexado;
- scraping con browser automation si hiciera falta.

### Q27. Política exacta de degradación

El PRD dice que primero degrada el chatbot.

Falta decidir:

- qué significa degradar exactamente;
- si pasa a modo solo FAQ/context reducido;
- si se corta el uso nuevo o solo se limita el volumen;
- umbrales técnicos para activar esa degradación.

---

## 3.9 Preparación multi-candidate light

### Q28. Dónde introducir `candidate_id`

Falta definir:

- qué tablas lo necesitan desde el día 1;
- cuáles pueden asumir single-candidate por ahora;
- cómo evitar sobrecargar el diseño sin cerrarse el futuro.

### Q29. Separación de corpus, scoring y oportunidades por candidato

Si se quiere dejar el camino abierto, hay que decidir qué módulos deben nacer desacoplados ya.

---

## 4. Decisiones recomendadas antes de iniciar SDD detallado

Secuencia sugerida:

1. cerrar stack backend y modelo de jobs;
2. cerrar dedupe + republicación;
3. cerrar scoring base + umbrales;
4. cerrar contrato del chatbot y RAG stack;
5. cerrar seguridad admin + retención/logging;
6. cerrar observabilidad mínima y política de coste.

Con eso, recién ahí conviene escribir specs y designs finos por change.

---

## 5. Decisiones que NO hace falta cerrar todavía

Para evitar sobreingeniería, no hace falta cerrar ahora:

- topología futura de escalado;
- separación eventual a microservicios;
- multi-candidate real completo;
- filtros públicos complejos;
- API pública inexistente en V1.

---

## 6. Próximos artefactos recomendados tras resolver este documento

Una vez cerradas estas preguntas, los siguientes documentos candidatos son:

1. `architecture/data-model.md`
2. `architecture/scoring-design.md`
3. `architecture/rag-design.md`
4. `operations/security-abuse.md`
5. `operations/observability-costs.md`
6. primeros ADRs
7. primeras proposals/specs/designs/tasks de SDD
