# Parser boundary

`gaussian_guard.py` is a conservative sentinel parser, not a complete Gaussian input
or output grammar.

## Implemented input observations

- one Link 0 / route / title / charge-multiplicity / Cartesian-coordinate job;
- canonical element symbols or atomic numbers 1-118 and an electron-count/
  multiplicity parity check;
- `%Chk` and `%OldChk` labels;
- exact planned `method/basis` token, limited to the synthetic
  `B3LYP/6-31G(d)` parser profile;
- supported task keywords `Opt` and `Freq`;
- checkpoint-read sentinels `Guess=Read`, `ChkBasis`, and `ReadFC` with explicit
  Cartesian geometry;
- explicit block sentinels for unprofiled methods and workflows.

It does not validate Z-matrices, basis/ECP blocks, internal coordinate constraints,
Link1 chains, route keyword compatibility, method availability, or every Gaussian
syntax rule. A pass means only that the supported subset matched the plan.

## Implemented output observations

- Gaussian 16 revision sentinel;
- normal/error termination sentinels;
- final SCF-energy sentinel plus a narrow list of known SCF non-convergence sentinels;
- optimization-completed sentinel;
- frequency-number sentinels and negative-frequency count.

It does not authenticate the output, recompute energies or Hessians, parse every link,
verify checkpoint contents, distinguish all convergence pathologies beyond the
implemented failure sentinels, or validate
physics. Hash binding and external execution records remain required.

The execution-record checker validates exact fields and plan/input/output byte/hash relationships. It
does not verify a signature, authenticate the issuer, or resolve the referenced
environment, authorization, or checkpoint. Those remain activation blockers.

## Conservative consequences

- Multiple normal terminations are blocked because this candidate cannot bind a
  multi-link chain.
- Multiple route sections or `--Link1--` are blocked.
- Any unprofiled feature is blocked even if Gaussian itself might support it.
- Any route token outside the exact model chemistry, `Opt`, `Freq`, `Guess=Read`,
  `ChkBasis`, and `ReadFC` allowlist is blocked. `Geom=Check` remains unsupported
  because this profile requires explicit Cartesian geometry.
- Plain `Opt Freq` is registered only for a minimum candidate. Transition-state
  optimization is blocked until a dedicated `Opt=TS`-family parser and real fixture
  profile are reviewed; a frequency-only job may still test an already supplied
  transition-state candidate.
- A missing sentinel is `needs_evidence` or `local_gate_blocked`, never an inferred
  pass.
