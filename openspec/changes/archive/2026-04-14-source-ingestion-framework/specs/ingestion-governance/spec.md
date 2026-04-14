# Delta for Ingestion Governance

## MODIFIED Requirements

### Requirement: Source governance and adapter contract
The system MUST govern ingestion through an adapter-agnostic framework that starts from a shared `SourceAdapter` contract and job/run execution model. Sources MAY be onboarded incrementally, but every execution SHALL create a traceable run with status, timestamps, counters, and categorized errors. Source-side filtering SHOULD be used only as an optimization when supported, while internal hard filters remain the canonical authority before downstream scoring.
(Previously: The requirement anchored first execution to InfoJobs and only stated minimal adapter/run governance.)

#### Scenario: First governed source execution
- GIVEN an approved source is configured
- WHEN an ingestion run starts
- THEN the run is recorded through the shared job/run governance model

#### Scenario: Source filters are insufficient
- GIVEN a captured offer bypasses source filtering
- WHEN internal eligibility is evaluated
- THEN hard filters still decide whether scoring can start

#### Scenario: Categorized run failure
- GIVEN a run ends with a classified error
- WHEN the outcome is stored
- THEN the run keeps the error category and terminal status
