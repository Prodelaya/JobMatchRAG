# Offer Canonicalization Baseline Specification

## Purpose
Establecer la base de dedupe, republicación y canonicidad.

## Requirements

### Requirement: Canonical offer and republication rules
The system MUST consolidate equivalent offers into one canonical offer with source-specific evidence. Canonical company resolution SHALL use cautious matching and keep a confidence notion. Field values MUST come from a defined source-of-truth preference with per-field overrides when another source is clearly better. A reposted offer SHALL become a new opportunity when time-gap and similarity rules indicate republication rather than a normal update.

#### Scenario: Same offer across portals
- GIVEN two sources describe the same active job
- WHEN canonicalization runs
- THEN one canonical offer is kept with linked source evidence

#### Scenario: Reposted opportunity
- GIVEN a near-identical job reappears after the republication window
- WHEN canonicalization evaluates history
- THEN a new opportunity is created instead of only updating the previous one
