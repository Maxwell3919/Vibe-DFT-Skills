# CP2K official manual snapshot: basis-methods

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/basis_sets.html
- Raw SHA-256: df2caa078b8e153a594aca99d2724374b987a391a5092b2cde2a295672996c25
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# Basis Sets

In CP2K’s Quickstep module, the Kohn-Sham orbitals are expanded in atom-centered Gaussian basis functions. This is different from pure plane-wave codes: increasing the real-space grid [CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/MGRID.html#CP2K_INPUT.FORCE_EVAL.DFT.MGRID.CUTOFF "CP2K_INPUT.FORCE_EVAL.DFT.MGRID.CUTOFF") improves the auxiliary plane-wave representation of densities and potentials, but it does not by itself reach the complete basis set limit. For systematic convergence, the Gaussian basis quality and the grid parameters have to be considered together.

Basis sets are selected for each atomic [KIND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#cp2k-input-force-eval-subsys-kind). The files that contain the basis definitions are listed in [BASIS\_SET\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.BASIS_SET_FILE_NAME "CP2K_INPUT.FORCE_EVAL.DFT.BASIS_SET_FILE_NAME"). CP2K searches these files in the current directory and in the configured CP2K data directory.

```
&FORCE_EVAL
  &DFT
    BASIS_SET_FILE_NAME BASIS_MOLOPT
  &END DFT
  &SUBSYS
    &KIND O
      BASIS_SET DZVP-MOLOPT-GTH
    &END KIND
    &KIND H
      BASIS_SET DZVP-MOLOPT-GTH
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

## Basis Set Names

Many CP2K basis sets encode their purpose in the name:

-   `SZV`, `DZVP`, `TZVP`, `TZV2P`, and `QZVPP` indicate increasing basis quality.

-   `MOLOPT` basis sets are molecularly optimized Gaussian basis sets commonly used with GPW.

-   `SR` indicates short-range MOLOPT variants. They are less diffuse and often more efficient for large condensed-phase systems when the target property does not require diffuse functions.

-   `GTH` basis sets are intended for GTH pseudopotential calculations.

-   `q1`, `q4`, `q6`, and similar suffixes indicate the number of valence electrons represented by the matching pseudopotential.

-   `ae` basis sets are all-electron basis sets, commonly used with the GAPW method and `POTENTIAL ALL`.


For production calculations, use basis sets and pseudopotentials that were designed to work together. For example, `DZVP-MOLOPT-GTH` for oxygen is normally paired with `GTH-PBE-q6` in a PBE calculation, while UZH protocol basis sets from `BASIS_MOLOPT_UZH` are paired with corresponding entries from `POTENTIAL_UZH`. For new GPW production inputs, these UZH protocol pairs are the preferred starting point where available; the older MOLOPT/GTH libraries remain useful for compatibility and comparison with established inputs. The same `BASIS_MOLOPT_UZH` file also contains all-electron MOLOPT basis sets for GAPW simulations, such as `SVP-MOLOPT-GGA-ae`, `TZVPP-MOLOPT-GGA-ae`, and `QZVPP-MOLOPT-GGA-ae`, to be used with `POTENTIAL ALL`.

## Basis Set Roles

The keyword [BASIS\_SET](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.BASIS_SET "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.BASIS_SET") can carry an optional basis type. Without an explicit type, CP2K uses the primary orbital basis:

```
&KIND O
  BASIS_SET ORB DZVP-MOLOPT-GTH
&END KIND
```

This is equivalent to the more common short form:

```
&KIND O
  BASIS_SET DZVP-MOLOPT-GTH
&END KIND
```

Other basis roles are used by specific methods, for example:

-   `AUX_FIT` for the auxiliary density matrix method.

-   `RI_AUX` for resolution-of-the-identity correlation methods.

-   `LRI` for local resolution-of-the-identity approaches.


The method-specific documentation usually states which auxiliary basis is required.

## Convergence and Practical Choices

Start with a basis set that is appropriate for the target accuracy, then converge the grid parameters. For many routine condensed-phase GPW calculations, double-zeta or triple-zeta MOLOPT basis sets are common starting points. For new setups, first check whether a matching UZH protocol basis and pseudopotential pair is available. Accurate energy differences, weak interactions, response properties, and post-Hartree-Fock methods may require larger or more specialized basis sets.

Diffuse basis functions can improve accuracy for molecular anions, excited states, polarizabilities, and weak interactions, but they also increase the cost and may make the overlap matrix more ill-conditioned. In periodic calculations, diffuse functions can also increase the number of periodic images that have to be considered.

For a simple tested example, see [Run a First Calculation](https://manual.cp2k.org/cp2k-2026_2-branch/getting-started/first-calculation.html).

## See Also

-   [https://en.wikipedia.org/wiki/Gaussian\_orbital](https://en.wikipedia.org/wiki/Gaussian_orbital)

-   [https://www.cp2k.org/basis\_sets](https://www.cp2k.org/basis_sets)

-   [https://www.cp2k.org/tools:cp2k-basis](https://www.cp2k.org/tools:cp2k-basis)

-   [VandeVondele2007](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#vandevondele2007)

-   [Iannuzzi2026](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#iannuzzi2026)
