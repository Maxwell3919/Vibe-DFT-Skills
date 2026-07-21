# Gaussian input and checkpoint workflows

Use this reference to draft or audit one Gaussian 16 job step. Treat it as a
provider-documented planning layer, not as guard support or execution authorization.

## Contents

1. Input-section map
2. Link 0 and resource identity
3. Route and model chemistry
4. Molecule specification
5. Keyword-driven additional sections
6. Checkpoint consumers and restarts
7. Derived-file handoff
8. Input audit record

## 1. Build the input-section map

Write the sections in provider order:

1. optional Link 0 commands (`%...`), with no blank-line terminator;
2. route section beginning with `#`, terminated by a blank line;
3. title section, terminated by a blank line;
4. molecule specification, terminated by a blank line;
5. keyword-driven additional sections, each with its documented terminator.

Omit title and molecule specification only when `Geom=AllCheck` explicitly retrieves
both from a compatible checkpoint. With `Geom=Checkpoint`, still supply charge and
multiplicity. Map every route keyword to any additional section it requires before
writing the file. A syntactically valid blank line in the wrong place changes section
ownership and must block the audit.

Keep the title non-sensitive and within the public input page's five-line limit. Treat
it as a label only; Gaussian does not interpret it as method, structure, or task
evidence.

Do not rely on the provider's empty-route `HF/STO-3G SP` behavior. Record it only as a
documented default and require an explicit method, basis, and task for scientific work.

First-party anchors: `g16-input`, `g16-route`, `g16-molspec`, `g16-geom`.

## 2. Audit Link 0 and resource identity

- Treat `%Mem` as an execution resource request, not a convergence parameter. Record
  its units and reconcile it with the platform/scheduler limit.
- Prefer the installed revision's documented CPU directive. Record `%CPU` or legacy
  `%NProcShared` exactly; never infer availability from a requested count.
- Give `%Chk` a private, portable label and a declared role. Keep the real path in the
  trusted execution layer, not in a public report.
- Interpret `%OldChk=parent` as copying the parent checkpoint into the current `%Chk`
  at the start of the job step. Bind both parent and child identities; do not treat it
  as an in-place continuation.
- Treat `%RWF`, `%Int`, scratch retention, Linda, GPU/CPU affinity, and `Default.Route`
  as platform-specific execution concerns. Resolve their precedence and retention
  policy on the licensed host before launch.
- Never assume that a larger `%Mem`, processor count, or scratch allocation improves
  scientific accuracy. Validate performance separately from the acceptance gates.

First-party anchors: `g16-link0`, `g16-running`.

## 3. Freeze route and model chemistry

Record the full route as structured intent before rendering text:

- job type and each option;
- electronic-structure method and all modifiers;
- orbital basis for every element;
- ECP and replaced-core count where applicable;
- density-fitting basis and pure/Cartesian function convention;
- SCF, integral-grid, symmetry, relativistic, dispersion, and solvent choices;
- requested properties, print level, and checkpoint consumers.

For `Gen`, `GenECP`, `Pseudo=Cards`, `ExtraBasis`, or density-fitting input, inventory
the element coverage and exact source/provenance of every block. Do not copy a basis or
ECP from an unverified old input. For `ChkBasis`, verify that the parent contains the
intended orbital basis, ECP, pure/Cartesian convention, and density-fitting basis. Do
not specify a conflicting orbital basis with `ChkBasis`.

For DFT comparisons, hold the integration grid fixed. The public DFT page documents
`Integral=UltraFine` as the Gaussian 16 default and advises against smaller production
grids; this is provider guidance, not proof that UltraFine is converged for the target.

First-party anchors: `g16-basissets`, `g16-chkbasis`, `g16-dft`, `g16-scf`.

## 4. Audit the molecule specification

Require an explicit signed total charge and positive spin multiplicity. Verify the
electron-count/multiplicity parity, but do not confuse parity with the intended
electronic state. Record the scientific rationale for open-shell, broken-symmetry,
fragment, or excited-state occupations separately.

For Cartesian input, preserve atom order, element identity, units, and coordinates.
For Z-matrix or mixed input, preserve variable definitions, references, and frozen
status. Block any handoff that changes atom order across QST2/QST3 structures,
fragment definitions, constraints, or downstream atom-indexed analysis.

Treat fragment charges/multiplicities, isotope/nuclear properties, ghost atoms,
periodic translation vectors, MM atom types, and PDB residue fields as distinct
extensions. Do not silently strip or synthesize them. Require a dedicated profile for
each such workflow.

First-party anchor: `g16-molspec`.

## 5. Inventory keyword-driven additional sections

Check the official input section-order table for the exact keyword combination. Common
examples include:

| Route feature | Additional input to bind |
|---|---|
| `Opt=ModRedundant` or selected GIC routes | constraints, scans, or GIC definitions |
| `Opt=QST2` / `QST3` | second/third title and molecule specification, in identical atom order |
| `Gen` / `GenECP` / `Pseudo=Cards` | basis and/or ECP blocks with complete element coverage |
| `SCRF=Read` | PCM parameters and any user-defined solvent data |
| `Guess=Alter`, `Cards`, or `Permute` | occupation/orbital input, including required open-shell sections |
| `Freq=ReadIsotopes`, `ReadAnharm`, or mode selection | temperature/pressure/isotopes or selected-mode controls |
| `IRC(Report=Read)` | atom-index coordinate list for reporting |

Reject an input that contains an orphan extra section, a required missing section, an
ambiguous terminator, or a structure-dependent section whose atom map is unbound.

## 6. Resolve each checkpoint consumer

Do not use “read checkpoint” as a single undifferentiated action. Resolve the exact
consumer:

| Consumer | Provider-documented role | Required audit |
|---|---|---|
| `Geom=Checkpoint` | read molecule specification; charge/multiplicity remain input | geometry producer, atom identity/order, charge/multiplicity compatibility |
| `Geom=AllCheck` | read title, charge/multiplicity, and molecule specification | all retrieved fields and any additional-section ordering |
| `Guess=Read` | use checkpoint orbitals as the initial guess | method/basis/geometry projection compatibility and intended state |
| `Guess=Restart` | start a new SCF from saved restart data after geometry/basis change | distinguish from `SCF=Restart`; verify producer and compatibility |
| `SCF=Restart` | continue the interrupted SCF state | same calculation identity and saved restart data |
| `ChkBasis` | retrieve basis/ECP and related conventions | exact parent basis inventory; no conflicting basis token |
| `Opt=ReadFC` / `RCFC` | retrieve an initial Hessian/internal or Cartesian force constants | force-constant producer, level, geometry, coordinate compatibility |
| `Opt=Restart` | continue a checkpointed optimization | original optimization type/options plus new immutable output identity |
| `Freq=ReadFC` | repeat mode/thermochemical analysis from saved force constants | same Hessian/geometry/masses plus explicit new analysis conditions |
| `TD=Read` / `Restart` | reuse TD state guesses or resume TD iterations | same basis for `TD=Read`, state-space definition, root/state identity |

Never combine incompatible checkpoint consumers merely because the same `.chk` file
exists. Require the exact parent hash, producer input/output hashes, Gaussian revision,
and role-specific metadata.

## 7. Bind derived-file handoffs

For `formchk`, record `.chk -> .fchk` as a representation-conversion edge. For
`cubegen`, record `.fchk -> .cube` with quantity selector, orbital/state or density,
grid origin/vectors/counts, units/format, and output hash. Keep all three artifacts
private unless their structures and electronic data are cleared for disclosure.

Treat a formatted checkpoint or cube as derived data, not independent validation.
Before passing an `.fchk`, `.wfn`, `.wfx`, or cube to Multiwfn or another consumer,
record:

- Gaussian producer revision and complete model chemistry;
- charge, multiplicity, geometry identity, and electronic state;
- density/wavefunction type and requested population/state convention;
- conversion utility and exact parent/child hashes;
- known omissions or unsupported fields in the consumer format.

First-party anchors: `g16-formchk`, `g16-cubegen`.

## 8. Emit an input audit record

Return at least:

1. exact input hash and byte count;
2. section map and termination status;
3. Link 0 resource/checkpoint declarations;
4. complete route intent and provider source IDs;
5. structure hash, atom-order map, charge, and multiplicity;
6. basis/ECP/solvent/additional-section provenance;
7. every checkpoint input/output role and lineage edge;
8. guard support and native validation state;
9. blocking unknowns and the smallest safe next action.

Do not echo private coordinates, route titles, host paths, checkpoint content, or
licensed material in a public audit.
