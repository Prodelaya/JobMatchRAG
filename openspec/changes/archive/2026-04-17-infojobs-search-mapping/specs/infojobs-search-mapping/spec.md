# InfoJobs Search Mapping Specification

## Purpose

Define how canonical role-intent families become auditable InfoJobs execution plans without making provider params the semantic authority.

## Requirements

### Requirement: Family-driven bilingual execution plans

The system MUST build InfoJobs plans from canonical role-intent families centered on internal tools, automation, and applied AI for employees. Each family SHALL keep separate Spanish and English baselines, MAY add justified mixed combinations, and MUST keep technologies as reinforcement or tactical probes rather than the primary axis. Representative role variants SHALL include titles such as AI Engineer, AI Automation Engineer, Automation Builder, Internal Tools Developer, Desarrollador Python de automatización/IA, and nearby equivalents. `q` MUST be important but not exclusive, and Odoo MUST NOT become the primary family axis.

#### Scenario: Canonical family becomes bilingual plan
- GIVEN a canonical family for internal automation with applied AI intent
- WHEN the mapper produces InfoJobs queries
- THEN it emits separate ES and EN baselines
- AND any mixed query is recorded as justified rather than implicit

### Requirement: Reliable pushdown with explicit degradation

The system MUST push down only InfoJobs filters considered reliably useful: `q`, clearly reliable geography filters, limited modality-related filters, `experienceMin`, `sinceDate`, `category`, `subcategory`, and `teleworking`. `experienceMin` SHALL be treated as a partial-but-strong signal, not sole semantic authority; `sinceDate` SHALL be optimization only; `category` and `subcategory` SHALL be contextual only; `teleworking` SHALL be support-only and never decisive alone. Fine-grained modality semantics and hard exclusions MUST remain post-fetch. The mapper MAY add light origin-side exclusions for obviously bad query combinations, but MUST NOT use aggressive exclusion.

#### Scenario: Provider filter is only partially trustworthy
- GIVEN the target excludes roles above three years and values textual seniority evidence
- WHEN the mapper uses `experienceMin`
- THEN the param is emitted only as a strong hint
- AND the semantic exclusion remains pending for post-fetch evaluation

#### Scenario: Optimization filter cannot redefine semantics
- GIVEN a run narrows capture with `sinceDate` and `teleworking`
- WHEN the execution plan is generated
- THEN those params are marked as optimization/support only
- AND modality or freshness authority does not move from JobMatchRAG to InfoJobs

### Requirement: Auditability of mapped plans

The system MUST record, per emitted InfoJobs query, the family, language baseline, chosen terms, technical reinforcements, pushed-down filters, degradations, and what remains for post-fetch validation.

#### Scenario: Degraded mapping remains explainable
- GIVEN a family cannot be fully expressed with provider params
- WHEN the mapper emits the execution plan
- THEN the trace records the missing semantics as degradations
- AND auditors can see which checks still run after fetch
