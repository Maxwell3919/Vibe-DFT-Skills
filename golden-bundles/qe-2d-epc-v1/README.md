# QE 2D phonon–EPC–Tc synthetic golden bundle

This directory contains a deterministic synthetic fixture for the Vibe-DFT-Skills QE two-dimensional electron–phonon coupling validator.

It tests repository behavior only:

- SCF, NSCF, phonon, and EPC stage identity and parent lineage;
- pseudopotential-set identity;
- cutoff, k-mesh, q-mesh, smearing, and vacuum convergence declarations;
- q-point weight closure;
- numerical integration of `alpha2F(omega)` to `lambda` and `omega_log`;
- q-resolved and mode-resolved lambda decomposition closure;
- two-dimensional acoustic, ZA-mode, and imaginary-mode gates;
- explicit external treatment of `mu*`;
- Allen–Dynes modified McMillan `Tc` recomputation;
- synthetic-evidence claim ceilings.

The fixture does not contain Quantum ESPRESSO output, a real material, a native executable run, or a superconducting prediction. Passing validation supports at most `technical_run_gates_only`.

Regenerate or validate with:

```text
python3 tools/validate_qe_2d_epc.py golden-bundles/qe-2d-epc-v1/evidence.json
```

The expected analytic values are:

```text
lambda       = 0.8632857142857143
omega_log    = 17.071652491805146 meV
mu_star      = 0.1
Tc           = 10.764537564017099 K
```

These numbers belong only to the synthetic spectral function in `evidence.json`.
