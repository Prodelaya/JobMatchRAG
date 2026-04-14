# Políticas y controles — JobMatchRAG

## 1. Propósito

Este documento fija los guardrails operativos mínimos de V1: retención, backups, degradación, superficie administrativa y baseline de privacidad/seguridad.

No es un runbook detallado. Es la política base que las verticales futuras deben obedecer.

## 2. Política de retención por clase de dato

La foundation define retención diferenciada, no un TTL único para todo.

| Clase de dato | Base mínima de retención |
|---|---|
| `RawOfferSnapshot` | 30 días |
| logs de run / trazabilidad operativa | 90 días |
| errores relevantes | 180 días |
| métricas agregadas | indefinida |

### Principios de retención

- se conserva lo suficiente para auditar, depurar y recuperar la operación;
- no se guarda “todo para siempre” por comodidad;
- cada limpieza debe respetar la clase de dato, no barrer a ciegas;
- borrar datos viejos no debe romper métricas agregadas ni trazabilidad mínima.

## 3. Expectativas de backup

Los backups deben cubrir la **fuente de verdad operativa** del sistema.

### Qué deben soportar los backups

Como mínimo, deben permitir:

- recuperar estado operativo sin depender solo de recomputación;
- restaurar histórico relevante de runs y decisiones;
- sostener continuidad de dashboard, scoring y operación básica tras un incidente.

### Boundary de backup

La foundation todavía NO cierra la frecuencia exacta, la tecnología ni RTO/RPO detallados. Pero sí cierra algo más importante: confiar solo en “lo recalculamos después” NO alcanza.

## 4. Orden de degradación controlada

Cuando el sistema enfrente presión de coste o fiabilidad, la degradación debe empezar por la capacidad menos crítica para la utilidad central.

### Orden de degradación requerido

1. recruiter chat;
2. capacidades accesorias ligadas al chat;
3. solo después, si hiciera falta, componentes core de operación.

### Regla de protección

La ingesta, el scoring, el dashboard y Telegram son parte del valor principal del producto. Por eso NO deben caer antes que recruiter chat.

## 5. Operaciones solo de admin

Las acciones operativas internas pertenecen a una superficie protegida y separada de lo público.

### Operaciones baseline solo para admin

Entre las operaciones que deben quedar detrás de esa barrera están:

- lanzar runs de fuentes;
- reprocesar etapas internas;
- disparar tareas de mantenimiento u operación;
- futuras acciones sobre corpus, umbrales o configuración sensible.

### Reglas de separación de superficies

- la UI o las rutas públicas no ejecutan acciones administrativas;
- el acceso admin debe ser dedicado;
- la superficie debe ser **MFA-ready**;
- las rutas protegidas no se mezclan con la experiencia pública de portfolio.

## 6. Base mínima de guardrails para `source-ingestion`

El framework común de ingesta debe aplicar guardrails operativos por defecto antes de cualquier adapter concreto:

- retries acotados por run;
- alcance acotado del run (fetch calls y/o items) para evitar loops ciegos;
- cierre explícito `partial` cuando hubo material usable pero el run terminó degradado;
- ejecución rate-limit-aware que registre observaciones del límite encontrado.

### Intención de la política de guardrails

- los límites existen para contener riesgo operativo, no para imponer umbrales mágicos del proveedor;
- una política `retryable` NO autoriza reintentos infinitos;
- un run degradado debe seguir siendo auditable aunque entregue material usable;
- los umbrales finos de backoff/cadencia siguen abiertos para verticales operativas posteriores.

## 7. Base mínima de privacidad y seguridad

La foundation fija una política base prudente:

- retención mínima suficiente por clase de dato;
- separación entre lectura pública y operación protegida;
- protección explícita de acciones sensibles;
- conservación de trazabilidad operativa relevante;
- reducción de exposición innecesaria de internals hacia la superficie pública.

### Regla de disclosure público/privado

La transparencia pública del sistema es valiosa, pero no justifica exponer:

- detalles internos completos de scoring;
- trazas operativas sensibles;
- controles administrativos;
- señales que faciliten abuso o interpretación incorrecta del sistema.

## 8. Relación de políticas con otros documentos foundation

Este documento depende y complementa a:

- `docs/architecture/system-overview.md` para boundaries público/protegido;
- `docs/architecture/ingestion-and-sources.md` para trazabilidad de runs y errores;
- `docs/architecture/scoring-foundation.md` para la prioridad del core de matching sobre capacidades secundarias;
- `docs/PRD-JobMatchRAG.md` para la degradación del recruiter chat antes del core.

## 9. Boundaries para cambios verticales futuros

Las siguientes verticales deben implementar sin reabrir estas reglas:

- retención por clase de dato con ventanas ya cerradas;
- backups sobre la fuente de verdad operativa;
- degradación comenzando por recruiter chat;
- operaciones internas detrás de una superficie admin dedicada;
- guardrails de ingesta con retries acotados, alcance limitado y cierre `partial` explícito;
- base mínima de privacidad/seguridad alineada con exposición pública limitada.

El detalle técnico operativo adicional debe expandir esta base sin reabrirla, tomando `docs/operations/observability-and-security.md` como referencia para métricas, alertas, audit trail y controles de superficie protegida.
