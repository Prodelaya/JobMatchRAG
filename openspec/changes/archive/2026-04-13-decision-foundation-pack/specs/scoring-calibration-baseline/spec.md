# Scoring Calibration Baseline Specification

## Purpose
Formalizar filtros previos, scoring híbrido y umbrales base.

## Requirements

### Requirement: Hard filters before hybrid scoring
The system MUST reject clearly incompatible offers before scoring, including disallowed geography/modality, seniority above 3 years, incompatible roles, and consultoras unless internal-work evidence is clear. Offers that pass SHALL receive rule-based scoring first and an LLM adjustment second. Explicit evidence MUST outweigh inferred evidence. Dashboard eligibility starts after hard filters; Telegram alerting SHALL start at score 70, with `buena` 70-84 and `prioritaria` 85-100.

#### Scenario: Offer rejected pre-score
- GIVEN an offer needs >3 years and incompatible modality
- WHEN eligibility is checked
- THEN the offer is excluded before scoring

#### Scenario: Offer passes and alerts
- GIVEN an offer passes hard filters and ends with score 88
- WHEN publication runs
- THEN it appears in the dashboard as prioritaria and triggers Telegram
