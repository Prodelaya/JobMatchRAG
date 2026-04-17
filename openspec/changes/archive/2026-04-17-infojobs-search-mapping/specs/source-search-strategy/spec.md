# Delta for Source Search Strategy

## MODIFIED Requirements

### Requirement: Canonical capture profile authority

The system MUST define a canonical `capture profile` as the semantic source of truth. It SHALL include strongly bilingual search families for (a) internal automation with explicit AI/LLM/agent intent, (b) internal automation without explicit AI, and (c) adjacent Odoo opportunities. Odoo MUST be treated as adjacent rather than core, and internal automation roles without explicit AI MAY remain eligible. The handoff to provider mapping SHALL preserve family intent, language baseline, and technical reinforcements as canonical semantics rather than provider taxonomy.
(Previously: the requirement established canonical families, but did not explicitly define the handoff contract for family/language/reinforcement semantics into provider mapping.)

#### Scenario: Capture profile is reviewed
- GIVEN a source execution is configured
- WHEN semantic search intent is inspected
- THEN the capture profile names the three canonical families
- AND provider params are not treated as semantic authority

#### Scenario: Family handoff reaches provider mapping
- GIVEN a canonical family includes Spanish baseline terms plus Python/API reinforcement
- WHEN the profile is handed to InfoJobs mapping
- THEN family, language, and reinforcement intent remain canonical metadata
- AND the provider query is treated only as a translated execution plan
