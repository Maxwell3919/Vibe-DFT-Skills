# CP2K official manual snapshot: pseudopotential-methods

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/pseudopotentials.html
- Raw SHA-256: 2826d3f74fdbae757593442368122d1543a56275520a5ed8d07fb4adb1062ac6
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# Pseudopotentials

Most GPW calculations in CP2K use norm-conserving Goedecker-Teter-Hutter ([GTH](https://manual.cp2k.org/cp2k-2026_2-branch/acronyms.html#term-GTH)) pseudopotentials. A pseudopotential removes chemically inactive core electrons from the explicit electronic problem and represents their effect on the valence electrons through an effective potential. This reduces the number of electrons and avoids the very hard core density that would otherwise require extremely fine grids.

Pseudopotential files are selected in [POTENTIAL\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html#CP2K_INPUT.FORCE_EVAL.DFT.POTENTIAL_FILE_NAME "CP2K_INPUT.FORCE_EVAL.DFT.POTENTIAL_FILE_NAME"), and the actual potential is selected for each atomic [KIND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#cp2k-input-force-eval-subsys-kind) with [POTENTIAL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.POTENTIAL "CP2K_INPUT.FORCE_EVAL.SUBSYS.KIND.POTENTIAL"):

```
&FORCE_EVAL
  &DFT
    POTENTIAL_FILE_NAME GTH_POTENTIALS
  &END DFT
  &SUBSYS
    &KIND O
      POTENTIAL GTH-PBE-q6
    &END KIND
    &KIND H
      POTENTIAL GTH-PBE-q1
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

The suffix `q6` in `GTH-PBE-q6`, for example, means that six valence electrons are treated explicitly. The chosen basis set should match this valence configuration; for oxygen, a common matching basis is `DZVP-MOLOPT-GTH`.

## Choosing a Pseudopotential

Use a pseudopotential generated for the exchange-correlation functional family used in the calculation. For example, `GTH-PBE-q6` is a natural choice for PBE calculations with oxygen. Mixing functional families can be acceptable for exploratory work in some cases, but it is not a systematic route to high accuracy.

The CP2K data directory contains several pseudopotential libraries:

-   `GTH_POTENTIALS` contains widely used GTH potentials for common GPW calculations.

-   `POTENTIAL_UZH` contains the UZH protocol GTH potentials designed to be used with matching UZH basis sets.

-   `NLCC_POTENTIALS` and `GTH_SOC_POTENTIALS` contain more specialized potentials.

-   `ECP_POTENTIALS` contains effective core potentials for Gaussian integral based calculations.


For new GPW production inputs, prefer a matching UZH protocol pair from `POTENTIAL_UZH` and `BASIS_MOLOPT_UZH` when it is available for the element and functional family. The older `GTH_POTENTIALS` library remains important for reproducing established calculations and for cases where a matching UZH setup is not available.

For all-electron calculations, use `POTENTIAL ALL` together with an all-electron basis set and the GAPW method:

```
&KIND O
  BASIS_SET SVP-MOLOPT-GGA-ae
  POTENTIAL ALL
&END KIND
```

## Consistency Checks

Useful checks when setting up a calculation are:

-   The basis set and pseudopotential should be available in the files named in the `DFT` section.

-   The pseudopotential valence charge should match the basis set suffix where such a suffix is used.

-   The exchange-correlation functional should be consistent with the pseudopotential family.

-   For heavy elements, decide whether a large-core, medium-core, small-core, or all-electron description is appropriate for the property of interest.


For a tested minimal GPW input using GTH pseudopotentials, see [Run a First Calculation](https://manual.cp2k.org/cp2k-2026_2-branch/getting-started/first-calculation.html).

## See Also

-   [https://en.wikipedia.org/wiki/Pseudopotential](https://en.wikipedia.org/wiki/Pseudopotential)

-   [https://cp2k.org/static/potentials/](https://cp2k.org/static/potentials/)

-   [https://www.cp2k.org/tools:cp2k-basis](https://www.cp2k.org/tools:cp2k-basis)

-   [Goedecker1996](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#goedecker1996)

-   [Hartwigsen1998](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#hartwigsen1998)

-   [Krack2005](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#krack2005)

-   [Iannuzzi2026](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#iannuzzi2026)
