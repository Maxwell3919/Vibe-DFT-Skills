# CP2K official manual snapshot: band-optimizer

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/OPTIMIZE_BAND.html
- Raw SHA-256: cf8ac3605c671b35bbd72bd385f17ee22626779d431be6973d4c4430f43150c8
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# OPTIMIZE\_BAND

**Section can be repeated.**

Specify the optimization method for the band \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_neb.F#L235)\]

Subsections

-   [DIIS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/OPTIMIZE_BAND/DIIS.html)
-   [MD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/OPTIMIZE_BAND/MD.html)

## Keywords

-   [OPTIMIZE\_END\_POINTS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/OPTIMIZE_BAND.html#CP2K_INPUT.MOTION.BAND.OPTIMIZE_BAND.OPTIMIZE_END_POINTS "CP2K_INPUT.MOTION.BAND.OPTIMIZE_BAND.OPTIMIZE_END_POINTS")

-   **[OPT\_TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/OPTIMIZE_BAND.html#CP2K_INPUT.MOTION.BAND.OPTIMIZE_BAND.OPT_TYPE "CP2K_INPUT.MOTION.BAND.OPTIMIZE_BAND.OPT_TYPE")**


## Keyword descriptions

### OPTIMIZE\_END\_POINTS*: logical* *\= F*

**Lone keyword:** `T`

If both end points of the band are also optimized alongside the rest of replica. This may be set to .TRUE. if both end points have already been optimized with the same FORCE\_EVAL, in which case the force on both end points will be reset to 0 on each step. Please note that both end points will always be included in NUMBER\_OF\_REPLICA and get NPROC\_REP processors allocated each for calculation in the same way as the rest of replica, regardless of this setting. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_neb.F#L374)\]

### OPT\_TYPE*: enum* *\= DIIS*

**Usage:** *OPT\_TYPE (MD|DIIS)*

**Valid values:**

-   `MD` Molecular dynamics-based optimizer

-   `DIIS` Coupled steepest descent / direct inversion in the iterative subspace


**Mentions:** ⭐[Troubleshooting](https://manual.cp2k.org/cp2k-2026_2-branch/getting-started/troubleshooting.html)

Specifies the type optimizer used for the band \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_neb.F#L362)\]
