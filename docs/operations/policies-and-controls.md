# Policies & Controls — JobMatchRAG

## 1. Purpose

Este documento fija los guardrails operativos mínimos de V1: retención, backups, degradación, superficie administrativa y baseline de privacidad/seguridad.

No es un runbook detallado. Es la política base que futuras verticales deben obedecer.

## 2. Retention Policy by Data Class

La foundation define retención diferenciada, no un TTL único para todo.

| Data class | Retention baseline |
|---|---|
| `RawOfferSnapshot` | 30 días |
| run logs / trazabilidad operativa | 90 días |
| errores relevantes | 180 días |
| métricas agregadas | indefinida |

### Retention principles

- se conserva lo suficiente para auditar, depurar y recuperar operación;
- no se guarda “todo para siempre” por comodidad;
- cada limpieza debe respetar la clase de dato, no barrer a ciegas;
- borrar datos viejos no debe romper métricas agregadas ni trazabilidad mínima.

## 3. Backup Expectations

Los backups deben cubrir la **fuente de verdad operativa** del sistema.

### What backups must support

Como mínimo, deben permitir:

- recuperar estado operativo sin depender solo de recomputación;
- restaurar histórico relevante de runs y decisiones;
- sostener continuidad de dashboard, scoring y operación básica tras incidente.

### Backup boundary

La foundation NO cierra todavía frecuencia exacta, tecnología ni RTO/RPO detallados. Pero sí cierra algo más importante: confiar solo en “lo recalculamos después” NO alcanza.

## 4. Graceful Degradation Order

Cuando el sistema enfrente presión de coste o fiabilidad, la degradación debe empezar por la capacidad menos crítica para la utilidad central.

### Required degradation order

1. recruiter chat;
2. capacidades accesorias ligadas al chat;
3. solo después, si hiciera falta, componentes core de operación.

### Protection rule

La ingesta, el scoring, el dashboard y Telegram son parte del valor principal del producto. Por eso NO deben caer antes que recruiter chat.

## 5. Admin-Only Operations

Las acciones operativas internas pertenecen a una superficie protegida y separada de lo público.

### Admin-only baseline operations

Entre las operaciones que deben quedar detrás de esa barrera están:

- lanzar runs de fuentes;
- reprocesar etapas internas;
- disparar tareas de mantenimiento u operación;
- futuras acciones sobre corpus, umbrales o configuración sensible.

### Surface separation rules

- la UI o rutas públicas no ejecutan acciones administrativas;
- el acceso admin debe ser dedicado;
- la superficie debe ser **MFA-ready**;
- las rutas protegidas no se mezclan con la experiencia pública de portfolio.

## 6. Source-ingestion guardrails baseline

El framework común de ingesta debe aplicar guardrails operativos por defecto antes de cualquier adapter concreto:

- retries acotados por run;
- alcance acotado del run (fetch calls y/o items) para evitar loops ciegos;
- cierre explícito `partial` cuando hubo material usable pero el run terminó degradado;
- ejecución rate-limit-aware que registre observaciones del límite encontrado.

### Guardrail policy intent

- los límites existen para contener riesgo operativo, no para imponer thresholds mágicos de proveedor;
- una política retryable NO autoriza reintentos infinitos;
- un run degradado debe seguir siendo auditable aunque entregue material usable;
- los thresholds finos de backoff/cadencia siguen abiertos para verticales operativas posteriores.

## 7. Privacy and Security Baseline

La foundation fija una política base prudente:

- retención mínima suficiente por clase de dato;
- separación entre lectura pública y operación protegida;
- protección explícita de acciones sensibles;
- conservación de trazabilidad operativa relevante;
- reducción de exposición innecesaria de internals hacia la superficie pública.

### Public/private disclosure rule

La transparencia pública del sistema es valiosa, pero no justifica exponer:

- detalles internos completos de scoring;
- trazas operativas sensibles;
- controles administrativos;
- señales que faciliten abuso o interpretación incorrecta del sistema.

## 8. Policy Relationship with Other Foundation Docs

Este documento depende y complementa a:

- `docs/architecture/system-overview.md` para boundaries público/protegido;
- `docs/architecture/ingestion-and-sources.md` para trazabilidad de runs y errores;
- `docs/architecture/scoring-foundation.md` para prioridad del core de matching sobre capacidades secundarias;
- `docs/PRD-JobMatchRAG.md` para la degradación del recruiter chat antes del core.

## 9. Boundaries for Future Vertical Changes

Las siguientes verticales deben implementar sin reabrir estas reglas:

- retención por clase de dato con ventanas ya cerradas;
- backups sobre la fuente de verdad operativa;
- degradación comenzando por recruiter chat;
- operaciones internas detrás de superficie admin dedicada;
- guardrails de ingesta con retries acotados, bounded scope y cierre `partial` explícito;
- baseline de privacidad/seguridad alineada con exposición pública limitada.

El detalle técnico operativo adicional debe expandir esta base sin reabrirla, tomando `docs/operations/observability-and-security.md` como referencia para métricas, alertas, audit trail y controles de superficie protegida.
