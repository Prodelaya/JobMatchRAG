# Ingestion Governance Specification

## Purpose
Definir la gobernanza mínima de fuentes, runs y guardrails de captura.

## Requirements

### Requirement: Source governance and adapter contract
The system MUST start with InfoJobs official API as the first production source and SHALL keep an adapter contract ready for future sources. Each source execution MUST produce traceable run records with status and errors. Ingestion SHOULD apply source-side filtering where available, but product eligibility MUST still be enforced by internal hard filters before scoring.

#### Scenario: First source execution
- GIVEN the configured V1 source is available
- WHEN an ingestion run starts
- THEN the run is recorded against the InfoJobs source contract

#### Scenario: Source filters are insufficient
- GIVEN a captured offer bypasses source filtering
- WHEN internal eligibility is evaluated
- THEN hard filters still decide whether scoring can start
