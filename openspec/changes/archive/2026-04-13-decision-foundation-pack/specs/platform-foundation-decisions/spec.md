# Platform Foundation Decisions Specification

## Purpose
Fijar la base técnica y operativa mínima compartida.

## Requirements

### Requirement: Backend and protected operations foundation
The system MUST use Python with FastAPI as backend foundation and a minimal custom admin surface, not a public operations UI. Background operations SHALL run through Celery from V1. Admin access MUST require dedicated authentication, start MFA-ready, and remain separated from public routes. Retention SHALL differentiate operational data classes instead of using one global TTL.

#### Scenario: Protected admin action
- GIVEN an unauthenticated visitor
- WHEN requesting an admin operation
- THEN access is denied

#### Scenario: Background work
- GIVEN a scrape or reindex action is requested
- WHEN it is accepted
- THEN execution is delegated to background processing
