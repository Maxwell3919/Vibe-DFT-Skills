## Problem and failure mode

Describe the specific defect, missing boundary, or capability gap.

## Scope

Changed:

- 

Intentionally unchanged:

- 

## Evidence classification

- [ ] Repository-observed facts are separated from external-source claims.
- [ ] Tested behavior is separated from inference and temporary assumptions.
- [ ] Unresolved items are listed explicitly.

## Tests

Positive tests:

- 

Negative or blocked tests:

- 

Mutation or adversarial tests:

- 

Commands run:

```text
python3 tools/run_tests.py
python3 tools/validate_all_skills.py
python3 tools/audit_repository.py
git diff --check -- . ':(exclude)skills/qe-rigorous-calculations/references/official-*'
```

## Lifecycle and routing

- Lifecycle impact: none / planned->development / development->active / demotion
- Routing impact:
- Installation impact:
- Side effects enabled or changed:
- Activation evidence record, when applicable:

## Scientific claim boundary

- Claim ceiling before:
- Claim ceiling after:
- Numerical-convergence impact:
- Physical-validity impact:
- Scientific-acceptance impact:

## Contracts and lineage

- Contract identities or versions changed:
- Parent/child record relationships changed:
- Hash or identity semantics changed:
- Migration required:

## Privacy and license

- [ ] No credentials, private hosts/accounts, real local/server paths, restricted potentials, raw private calculation trees, or unpublished results are included.
- [ ] Fixture and source redistribution terms were reviewed.
- Privacy or license impact:

## Rollback

Describe how to revert the change without silently rewriting historical evidence.

## Remaining limitations

- 
