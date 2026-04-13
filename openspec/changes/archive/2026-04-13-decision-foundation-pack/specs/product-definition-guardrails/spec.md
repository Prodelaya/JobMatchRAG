# Product Definition Guardrails Specification

## Purpose
Definir el framing funcional V1 y los límites visibles del producto.

## Requirements

### Requirement: V1 product framing and visibility
The system MUST operate as personal job intelligence first: hard-filtered offers are ranked, shown in the public dashboard, and Telegram alerts are sent only for new offers with score >= 70. The dashboard SHALL expose a freshness disclaimer and default to recent visibility while preserving full history internally. Recruiter chat MUST stay secondary and answer only from Pablo profile context; if context is insufficient, it SHALL say so.

#### Scenario: Public V1 flow
- GIVEN a new offer passes hard filters and scores 82
- WHEN publication rules run
- THEN the offer appears in the dashboard and triggers one Telegram alert

#### Scenario: Chat without enough context
- GIVEN a recruiter asks about unsupported context
- WHEN the chat answers
- THEN it refuses speculation and states the context limit
