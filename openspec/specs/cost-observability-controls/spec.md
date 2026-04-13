# Cost Observability Controls Specification

## Purpose
Definir controles operativos mínimos para coste, salud y recuperación.

## Requirements

### Requirement: Minimum operational controls and graceful degradation
The system MUST expose minimum observability for runs, failures, alerts, and LLM/chat usage. Backups SHALL cover the operational source of truth and support recovery without depending on recomputation alone. Retention MUST keep run logs for 90 days, raw snapshots for 30 days, relevant errors for 180 days, and aggregated metrics indefinitely. When cost or reliability limits are hit, degradation SHALL begin with recruiter chat before core ingestion, scoring, dashboard, or Telegram flows.

#### Scenario: Cost pressure
- GIVEN LLM/chat usage reaches a degradation threshold
- WHEN protection rules activate
- THEN recruiter chat is reduced before core job intelligence stops

#### Scenario: Operational retention
- GIVEN retention cleanup runs
- WHEN data ages exceed class limits
- THEN each data class is pruned according to its configured retention window
