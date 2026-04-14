# Hoja de ruta vertical — JobMatchRAG

**Estado:** hoja de ruta viva de verticales
**Objetivo:** dejar visible el orden recomendado de changes, su dependencia principal y las reglas para ajustar la secuencia sin perder criterio.

---

## 1. Cómo usar este documento

Este roadmap sirve como guía operativa para saber:

- qué changes ya quedaron cerrados;
- cuál es el siguiente vertical recomendado;
- qué dependencias existen entre verticales;
- cuándo puede variar el orden.

No es un contrato rígido e inmutable. El orden puede cambiar si aparece una dependencia nueva real, un gap de discovery no resuelto o un change habilitador más chico que convenga insertar antes.

---

## 2. Reglas de secuencia

- El orden de abajo es **recomendado**, no obligatorio por sí mismo.
- Puede insertarse un change nuevo si discovery demuestra que falta una base real para el siguiente vertical.
- Un vertical puede dividirse en cambios más chicos si eso reduce riesgo o mezcla de scope.
- Un vertical no debe reabrir foundations ya cerradas salvo que exista un cambio explícito de estrategia.
- Si cambia el orden o aparece un nuevo change intermedio, este documento debe actualizarse en el mismo cambio.

---

## 3. Hoja de ruta actual

| Orden | Change | Estado | Depende de | Propósito |
| --- | --- | --- | --- | --- |
| 1 | `decision-foundation-pack` | cerrado | — | Cerrar foundations de producto, arquitectura, scoring, operaciones y documentación viva. |
| 2 | `project-tooling-bootstrap` | cerrado | `decision-foundation-pack` | Dejar un bootstrap Python ejecutable con `.venv`, `pytest`, `ruff`, `mypy` y un contrato de verify reusable. |
| 3 | `uv-bootstrap-alignment` | cerrado | `project-tooling-bootstrap` | Mini-change de alineación documental del bootstrap local con `uv + .venv`; recomienda `uv venv .venv` + `uv pip install -e .[dev]`, preserva el contrato `.venv/bin/python -m ...` y no agrega tooling nuevo ni capacidad funcional de ingesta. |
| 4 | `source-ingestion-framework` | cerrado | `uv-bootstrap-alignment` | Definir e implementar el framework común de fuentes, adapters, runs, errores, retries y límites operativos de ingesta. |
| 5 | `first-source-infojobs` | cerrado | `source-ingestion-framework` | Implementó la primera fuente real sobre InfoJobs API con adapter concreto, tests verdes, preservación raw `list/detail` y documentación viva alineada. |
| 6 | `offer-normalization-canonicalization` | pendiente | `first-source-infojobs` | Normalizar ofertas, consolidar evidencia, dedupe cross-source y reglas de republicación. |
| 7 | `rule-based-scoring` | pendiente | `offer-normalization-canonicalization` | Implementar filtros duros y scoring base explicable por reglas. |
| 8 | `llm-score-adjustment` | pendiente | `rule-based-scoring` | Añadir inferencia semántica acotada sin romper auditabilidad ni control de coste. |
| 9 | `telegram-alerts` | pendiente | `rule-based-scoring` | Notificar nuevas oportunidades con score suficiente y anti-duplicado. |
| 10 | `public-dashboard` | pendiente | `rule-based-scoring` | Publicar ofertas evaluadas con score, warnings, razones cortas y frescura. |
| 11 | `recruiter-rag-corpus` | pendiente | `decision-foundation-pack` | Definir y preparar el corpus permitido para recruiter chat. |
| 12 | `recruiter-chat-experience` | pendiente | `recruiter-rag-corpus` | Construir la experiencia conversacional acotada para recruiters. |
| 13 | `admin-operations-panel` | pendiente | `source-ingestion-framework`, `rule-based-scoring` | Exponer operaciones protegidas para runs, reprocesos, reintentos y visibilidad operativa. |
| 14 | `observability-and-ops-hardening` | pendiente | `source-ingestion-framework`, `telegram-alerts`, `public-dashboard` | Consolidar métricas, alertas, auditoría, seguridad y endurecimiento operativo. |

---

## 4. Cuándo puede cambiar esta hoja de ruta

Cambiar el orden o insertar un nuevo change es razonable si ocurre al menos una de estas condiciones:

- el siguiente vertical todavía tiene huecos reales que requieren un mini-change habilitador;
- aparece una dependencia transversal nueva (por ejemplo workflow local, auth, contrato de datos o tooling extra);
- el tamaño del vertical recomendado creció demasiado y conviene partirlo;
- un cambio posterior queda desbloqueado antes por menor riesgo y mayor valor.

Si eso pasa, el cambio debe explicitar:

1. qué vertical iba antes;
2. qué nuevo change se inserta o se adelanta;
3. por qué el nuevo orden reduce riesgo o aclara dependencias.

---

## 5. Próximo vertical recomendado

Hoy, el foco recomendado pasa a ser:

**abrir `offer-normalization-canonicalization`**

Razón: `first-source-infojobs` ya quedó cerrado y archivado con su spec principal sincronizada. El siguiente paso natural es transformar la evidencia cruda ya capturada en ofertas canónicas, deduplicadas y listas para scoring/publicación.
