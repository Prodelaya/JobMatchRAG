# Vertical Roadmap — JobMatchRAG

**Estado:** roadmap vivo de verticales  
**Objetivo:** dejar visible el orden recomendado de changes, su dependencia principal y las reglas para ajustar la secuencia sin perder criterio.

---

## 1. Cómo usar este documento

Este roadmap sirve como guía operativa para saber:

- qué changes ya quedaron cerrados;
- cuál es el siguiente vertical recomendado;
- qué dependencias existen entre verticales;
- cuándo puede variar el orden.

No es un contrato rígido e inmutable. El orden puede cambiar si aparece una dependencia nueva real, un gap de discovery no resuelto o un change habilitador más pequeño que convenga insertar antes.

---

## 2. Reglas de secuencia

- El orden de abajo es **recomendado**, no obligatorio por sí mismo.
- Puede insertarse un change nuevo si discovery demuestra que falta una base real para el siguiente vertical.
- Un vertical puede dividirse en cambios más pequeños si eso reduce riesgo o mezcla de scope.
- Un vertical no debe reabrir foundations ya cerradas salvo que exista un cambio explícito de estrategia.
- Si cambia el orden o aparece un nuevo change intermedio, este documento debe actualizarse en el mismo cambio.

---

## 3. Roadmap actual

| Orden | Change | Estado | Depende de | Propósito |
| --- | --- | --- | --- | --- |
| 1 | `decision-foundation-pack` | cerrado | — | Cerrar foundations de producto, arquitectura, scoring, operaciones y documentación viva. |
| 2 | `project-tooling-bootstrap` | cerrado | `decision-foundation-pack` | Dejar bootstrap Python ejecutable con `.venv`, `pytest`, `ruff`, `mypy` y contrato verify reutilizable. |
| 3 | `uv-bootstrap-alignment` | cerrado | `project-tooling-bootstrap` | Mini-change de alineación documental del bootstrap local con `uv + .venv`; recomienda `uv venv .venv` + `uv pip install -e .[dev]` y preserva el contrato `.venv/bin/python -m ...`. |
| 4 | `source-ingestion-framework` | cerrado | `uv-bootstrap-alignment` | Definir e implementar el framework común de fuentes, adapters, runs, errores, retries y límites operativos de ingesta. |
| 5 | `first-source-infojobs` | pendiente | `source-ingestion-framework` | Implementar la primera fuente real sobre InfoJobs API usando el framework común. |
| 6 | `offer-normalization-canonicalization` | pendiente | `first-source-infojobs` | Normalizar ofertas, consolidar evidencia, dedupe cross-source y reglas de republicación. |
| 7 | `rule-based-scoring` | pendiente | `offer-normalization-canonicalization` | Implementar hard filters y scoring base explicable por reglas. |
| 8 | `llm-score-adjustment` | pendiente | `rule-based-scoring` | Añadir inferencia semántica acotada sin romper auditabilidad ni control de coste. |
| 9 | `telegram-alerts` | pendiente | `rule-based-scoring` | Notificar nuevas oportunidades con score suficiente y anti-duplicado. |
| 10 | `public-dashboard` | pendiente | `rule-based-scoring` | Publicar ofertas evaluadas con score, warnings, razones cortas y freshness. |
| 11 | `recruiter-rag-corpus` | pendiente | `decision-foundation-pack` | Definir y preparar el corpus permitido para recruiter chat. |
| 12 | `recruiter-chat-experience` | pendiente | `recruiter-rag-corpus` | Construir la experiencia conversacional acotada para recruiters. |
| 13 | `admin-operations-panel` | pendiente | `source-ingestion-framework`, `rule-based-scoring` | Exponer operaciones protegidas para runs, reprocesos, reintentos y visibilidad operativa. |
| 14 | `observability-and-ops-hardening` | pendiente | `source-ingestion-framework`, `telegram-alerts`, `public-dashboard` | Consolidar métricas, alertas, auditoría, seguridad y endurecimiento operativo. |

---

## 4. Cuándo puede cambiar este roadmap

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

Hoy, el siguiente change recomendado es:

**`first-source-infojobs`**

Razón: `source-ingestion-framework` ya quedó cerrado y dejó lista la base reusable adapter-agnostic de jobs, runs, errores, guardrails y trazabilidad. El siguiente paso natural es `first-source-infojobs`, que ya puede implementar la primera fuente real sobre ese framework sin reabrir foundations ni mezclar el contrato común con detalles de proveedor antes de tiempo.
