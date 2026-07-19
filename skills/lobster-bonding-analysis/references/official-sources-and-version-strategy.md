# Official sources and version strategy

## Pinned provider

The candidate provider is **LOBSTER 5.1.1**, released 2024-09-26. The first-party download page identifies that version and date. The registration page states that use requires accepting a non-exclusive, non-transferable, revocable license for non-profit research, prohibits making the software or any part accessible to third parties without written consent, disclaims responsibility for results, and requires specified citations.

Primary sources:

- First-party download and version page: https://schmeling.ac.rwth-aachen.de/cohp/index.php?menuID=6
- First-party registration and license page: https://schmeling.ac.rwth-aachen.de/cohp/index.php?fileID=18&menuID=603
- COHP definition: R. Dronskowski and P. E. Blöchl, *J. Phys. Chem.* 1993, 97, 8617–8624, https://doi.org/10.1021/j100135a014
- Projected COHP definition: V. L. Deringer, A. L. Tchougréeff, and R. Dronskowski, *J. Phys. Chem. A* 2011, 115, 5461–5466, https://doi.org/10.1021/jp202489s
- LOBSTER framework: S. Maintz et al., *J. Comput. Chem.* 2013, 34, 2557–2567, https://doi.org/10.1002/jcc.23424
- Projection-quality developments: S. Maintz et al., *J. Comput. Chem.* 2016, 37, 1030–1035, https://doi.org/10.1002/jcc.24300
- Time-reversal, population analysis, and k-dependent COHP: R. Nelson et al., *J. Comput. Chem.* 2020, 41, 1931–1940, https://doi.org/10.1002/jcc.26353

The first-party download page documents that LOBSTER can derive projected COHP, COOP, and atom-projected DOS from VASP, ABINIT, or Quantum ESPRESSO plane-wave results. That statement establishes software capability, not adapter maturity. Public first-party pages do not publish the exact executable argv, complete `lobsterin` grammar, provider-specific file/settings contract, 5.1.1 completion/fatal markers, or complete output schemas; the download page directs authorized users to the bundled manual and examples. Those fields are `manual-required` and must not be filled from memory or third-party tutorials.

## Trust order

1. Exact 5.1.1 manual and examples shipped to an authorized licensee.
2. First-party 5.1.1 download/license pages.
3. The cited primary method papers for definitions and limitations.
4. Version-matched, legally reusable real artifacts with recorded hashes.
5. Community parsers only as independent comparison evidence, never as first-party syntax authority.

If these sources disagree, stop and record `LOB.VERSION.SOURCE_CONFLICT`. Do not resolve a conflict from memory or a newer/older manual.

## Version policy

- `5.1.1` is the only provider identity accepted by the candidate audit contract.
- `5.1.0`, `5.0.x`, later releases, development builds, and unversioned output are blocked until a separate parser and evidence profile is validated.
- A version string from a request is not enough. Real integration must bind the executable identity, authorization receipt, manual identity, and output header to the execution record.
- Parser success on the synthetic candidate format establishes only `synthetic-validated` maturity.
- Format compatibility is never inferred across patch, minor, DFT-provider, spin, or task boundaries.

## Scientific-source boundary

The method papers explain what projection, spilling, COHP, COOP, and related quantities mean. They do not prescribe a universal acceptable charge-spilling threshold for every system, basis, pressure, chemistry, or claim. Every audit therefore requires an explicit threshold and rationale supplied by the scientific plan. Passing that threshold remains a projection gate, not a chemical conclusion.

The repository does not reproduce the manual, basis files, binary, or licensed examples. Exact-byte verification of those private resources is an external activation blocker.
