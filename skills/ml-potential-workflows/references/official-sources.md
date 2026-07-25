# Official-source boundary

Use version-matched first-party documentation. These locators justify only the stated
workflow distinction; they do not prove a local installation, model, dataset, result
or license. The hash-bound machine records are
[`source-pack-seed.json`](source-pack-seed.json) and
[`source-pack-scope-catalog.json`](source-pack-scope-catalog.json); both remain
`blocked` because this Skill stores external receipts rather than official bodies.

## Exact authority split

| Authority | Exact identity | Reviewed boundary |
|---|---|---|
| MACE framework | tag `v0.3.16`, commit `4d2da09413ac1407f37cdbb6b81fa28e4c15655e` | The exact tag has no `docs/` tree. Its framework LICENSE is MIT and does not cover the separate docs branch or model artifacts. |
| MACE docs | docs-branch commit `bff7c94d8fbfdc3dde707ade12db5f36b97683b5` plus timestamped ReadTheDocs receipts | The branch identifies a 0.3.13-era corpus, `/en/v0.3.16/` is unavailable, and the branch uses an Academic Software License. Do not label it exact v0.3.16 docs. |
| NequIP | tag `v0.19.0`, commit `ea3ac14154338da83386be75d619b0cd964ffb42` | Exact source contains 68 docs pages; API completeness also depends on the exact code tree used by autodoc. Rolling ReadTheDocs differs and cannot replace the tag. |
| FairChem v1 | tag `fairchem_core-1.10.0`, commit `977a80328f2be44649b414a9907a1d6ef2f81e95` | The 60-path docs tree has generated AutoAPI references, one missing page, and binary assets. Repository MIT does not establish legacy checkpoint rights. |
| FairChem v2 | tag `fairchem_core-2.21.0`, commit `f47a0a6f0f594ea051b70091304864242df933e1` | The 95-path docs tree has 66 Markdown pages, 64 in MyST TOC and two source orphans. v2 is not interchangeable with v1. |
| UMA model repository | Hugging Face revision `f611b917d9c68566bbbeccbb0aa0f7cad1696cb2` public API receipt | Manual gating, `license:other`, model-card/reference-YAML access and checkpoint byte hashes remain unresolved. Names such as `uma-s-1p2.pt` are metadata only. |
| FairChem dataset/reference docs | exact FairChem v2.21.0 pages for OMol25, OMC25, OMat24, ODAC23, OC20, OC22 and OC25 | Page receipts record dataset-license and DFT-protocol statements only; they do not establish external archive identities or reference-software/potential/raw-output rights. |

## First-party workflow locators

| Provider | First-party locator | Bounded use |
|---|---|---|
| MACE | <https://github.com/ACEsuit/mace/releases/tag/v0.3.16> | Registered framework release identity. |
| MACE | <https://mace-docs.readthedocs.io/en/latest/guide/training.html>, <https://mace-docs.readthedocs.io/en/latest/guide/evaluation.html> | Rolling training/evaluation behavior only; version divergence remains explicit. |
| MACE | <https://mace-docs.readthedocs.io/en/latest/guide/foundation_models.html> | Rolling model index; each model family requires its own artifact identity and license. |
| NequIP | <https://github.com/mir-group/nequip/releases/tag/v0.19.0> | Exact release and breaking-change identity. |
| NequIP | <https://github.com/mir-group/nequip/tree/ea3ac14154338da83386be75d619b0cd964ffb42/docs> | Exact docs-source inventory used instead of silently treating rolling pages as v0.19.0. |
| FairChem v1 | <https://github.com/FAIR-Chem/fairchem/tree/977a80328f2be44649b414a9907a1d6ef2f81e95/docs> | Exact legacy docs source, with generated-page and binary-asset gaps preserved. |
| FairChem v2 | <https://github.com/FAIR-Chem/fairchem/tree/f47a0a6f0f594ea051b70091304864242df933e1/docs> | Exact v2 docs and dataset/reference-protocol page inventory. |
| FairChem | <https://fair-chem.github.io/fairchemv1-v2/> | Rolling explanation of the v1/v2 breaking boundary; exact tag sources remain authoritative. |
| UMA | <https://huggingface.co/api/models/facebook/UMA> | Public metadata only. Never use it as a checkpoint-byte hash or accepted model-card record. |

## Rights and evidence layers

Keep four independent records:

1. framework source and documentation license;
2. selected model card, custom terms, checkpoint identity and byte SHA-256;
3. exact dataset distribution identity, effective access terms and license;
4. reference-DFT software, pseudopotential/basis, raw-output and redistribution
   rights.

FairChem dataset pages reviewed at the exact v2.21.0 revision state CC-BY-4.0 and
describe these reference routes: OMol25 uses ORCA 6
`wB97M-V/def2-TZVPD`; OMC25 uses VASP PBE+D3; OMat24 uses VASP 5.4
PBE/PBE+U; ODAC23 uses VASP 5.4 PBE+D3; OC20 uses VASP 5.4 RPBE; OC22
uses VASP 5.4 PBE+U; and OC25 uses VASP 6.4 RPBE+D3. Those statements do not
grant ORCA/VASP software, PAW/POTCAR or other potential contents, private raw
outputs, or gated Argonne/Globus access.

Resolver rules:

1. Match the exact provider and version to the environment registry.
2. Treat docs as documented behavior only.
3. Resolve model cards, artifact byte hashes, custom terms and licenses independently.
4. Resolve dataset bytes and reference-DFT rights independently from repository MIT.
5. If a decisive config, unit, task-head, packaging, license or archive identity is
   absent, mark it unresolved.
6. Never copy provider documentation, model weights, dataset samples, serialized
   assets, restricted potentials or raw calculations into this candidate.

Regenerate or check the machine records only through the offline extractor. Installed
help and exact native fixtures must win if rolling docs drift; neither is present in
this development Skill.
