# Reporting workflow and role boundaries

## Roles

| Role | May do | Must not do |
| --- | --- | --- |
| Request owner | Choose purpose, language, sections, and selected claim IDs | Declare missing evidence passed |
| Evidence producer | Produce immutable calculation, artifact, campaign, source, or gate records | Rewrite adverse results for reporting |
| Deterministic reporting CLI | Check exact-byte identity, link claims, audit coverage, and render a local JSON draft | Authenticate source authority, accept science, or publish |
| Scientific reviewer | Judge bounded scientific claims against resolved evidence | Be impersonated by an agent field |
| Release owner | Decide privacy, license, editorial, and publication release | Infer acceptance from a rendering pass |
| External trust resolver | Authenticate human decisions and restricted/official sources | Be replaced by a self-declared bundle field |

## State separation

Maintain report-plan status, calculation application status, claim-map status, claim ceiling, scientific acceptance, source authority, citation completeness, publication readiness, and message-sending state independently. A plan or audit pass changes only the candidate-local report status.

## Fixed handoff

1. Consume immutable claim, artifact, and campaign refs.
2. Produce a candidate plan bound to the exact claim-map bytes.
3. Audit the unchanged plan.
4. Render a candidate package bound to the exact plan and audit bytes.
5. Submit those records to production bundle validation.
6. Obtain separate scientific and release decisions where required.
7. Let an authorized external system send or publish; this candidate never does so.
