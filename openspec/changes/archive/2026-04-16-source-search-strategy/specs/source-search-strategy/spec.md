# Source Search Strategy Specification

## Purpose

Define the canonical provider-agnostic capture profile, search families, and target-filter semantics that govern source ingestion before provider mapping, canonicalization, scoring, and LLM enrichment.

## Requirements

### Requirement: Canonical capture profile authority

The system MUST define a canonical `capture profile` as the semantic source of truth. It SHALL include strongly bilingual search families for (a) internal automation with explicit AI/LLM/agent intent, (b) internal automation without explicit AI, and (c) adjacent Odoo opportunities. Odoo MUST be treated as adjacent rather than core, and internal automation roles without explicit AI MAY remain eligible.

#### Scenario: Capture profile is reviewed
- GIVEN a source execution is configured
- WHEN semantic search intent is inspected
- THEN the capture profile names the three canonical families
- AND provider params are not treated as semantic authority

### Requirement: Canonical target filters

The system MUST apply canonical target filters for explicit/reliable incompatibilities only. It MUST discard offers that are explicitly senior/high-experience, explicitly incompatible with modality/geography policy, explicitly/reliably body-shopping oriented, or reliably older than 15 days. It MUST preserve ambiguous evidence for later review/scoring. Geography policy SHALL be onsite only in Madrid, remote anywhere in Spain, and hybrid in Madrid or elsewhere in Spain only when office attendance is under 3 days per month and the city is allowed by a maintained in-repo hybrid-eligibility dataset seeded from the user-provided April 2026 city list. Consultancy/body-shopping detection SHALL combine explicit/reliable textual signals with a curated provisional known-companies list, but a company-list hit alone MUST NOT trigger hard exclusion.

#### Scenario: Ambiguous modality survives
- GIVEN an offer references hybrid work in Spain without attendance details
- WHEN target filters are evaluated
- THEN the offer is preserved as ambiguous
- AND the incompatibility is not treated as explicit

#### Scenario: Curated hybrid city reference enables eligibility
- GIVEN an offer is hybrid outside Madrid with attendance under 3 days per month
- AND the city appears in the maintained in-repo hybrid-eligibility dataset
- WHEN target filters are evaluated
- THEN geography/modality remains eligible

#### Scenario: Known consultancy list alone stays ambiguous
- GIVEN an offer company matches the curated provisional known-companies list
- AND the posting lacks explicit/reliable consultancy or body-shopping language
- WHEN target filters are evaluated
- THEN the offer is preserved as ambiguous
- AND hard exclusion is not triggered

#### Scenario: Explicit consultancy evidence triggers exclusion
- GIVEN an offer includes explicit/reliable consultancy or body-shopping language
- WHEN target filters are evaluated
- THEN the offer is discarded as incompatible
- AND later scoring or LLM stages do not override that exclusion

### Requirement: Pushdown and post-fetch execution

Providers MAY execute supported target filters via pushdown. Unsupported target filters MUST be applied post-fetch inside JobMatchRAG without changing canonical semantics.

#### Scenario: Provider lacks seniority pushdown
- GIVEN a provider can filter by date but not semantic seniority
- WHEN ingestion runs
- THEN supported freshness narrowing MAY run provider-side
- AND senior/high-experience exclusion still runs post-fetch

### Requirement: Downstream handoff order

Canonical filtering and hard exclusions MUST run before downstream provider mapping handoff, scoring, and LLM distillation/enrichment. LLM enrichment MUST NOT replace canonical filtering, and later ranking MAY prefer explicit AI/LLM/agent integration over adjacent but still eligible automation roles.

#### Scenario: AI ranking stays downstream
- GIVEN two offers survive canonical filtering
- WHEN one has explicit AI integration and the other does not
- THEN both remain eligible for downstream stages
- AND any preference is deferred to later ranking/scoring
