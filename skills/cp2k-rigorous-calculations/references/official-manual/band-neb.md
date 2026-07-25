# CP2K official manual snapshot: band-neb

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND.html
- Raw SHA-256: 1efc9c5f25da266f97cd04fc08c8ac454c89d45bea66b7a2d4d34c0ee4e97657
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# BAND

**References:** [Elber1987](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#elber1987), [Jonsson1998](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#jonsson1998), [Henkelman2000b](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#henkelman2000b), [Henkelman2000](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#henkelman2000), [Trygubenko2004](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#trygubenko2004)

The section that controls a BAND run \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_neb.F#L66)\]

Subsections

-   [BANNER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/BANNER.html)
-   [CI\_NEB](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/CI_NEB.html)
-   [CONVERGENCE\_CONTROL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/CONVERGENCE_CONTROL.html)
-   [CONVERGENCE\_INFO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/CONVERGENCE_INFO.html)
-   [ENERGY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/ENERGY.html)
-   [FINAL\_BAND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/FINAL_BAND.html)
-   [OPTIMIZE\_BAND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/OPTIMIZE_BAND.html)
-   [PROGRAM\_RUN\_INFO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/PROGRAM_RUN_INFO.html)
-   [REPLICA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/REPLICA.html)
-   [REPLICA\_INFO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/REPLICA_INFO.html)
-   [STRING\_METHOD](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND/STRING_METHOD.html)

## Keywords

-   [ALIGN\_FRAMES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND.html#CP2K_INPUT.MOTION.BAND.ALIGN_FRAMES "CP2K_INPUT.MOTION.BAND.ALIGN_FRAMES")

-   [BAND\_TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND.html#CP2K_INPUT.MOTION.BAND.BAND_TYPE "CP2K_INPUT.MOTION.BAND.BAND_TYPE")

-   [K\_SPRING](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND.html#CP2K_INPUT.MOTION.BAND.K_SPRING "CP2K_INPUT.MOTION.BAND.K_SPRING")

-   [NPROC\_REP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND.html#CP2K_INPUT.MOTION.BAND.NPROC_REP "CP2K_INPUT.MOTION.BAND.NPROC_REP")

-   [NUMBER\_OF\_REPLICA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND.html#CP2K_INPUT.MOTION.BAND.NUMBER_OF_REPLICA "CP2K_INPUT.MOTION.BAND.NUMBER_OF_REPLICA")

-   [POT\_TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND.html#CP2K_INPUT.MOTION.BAND.POT_TYPE "CP2K_INPUT.MOTION.BAND.POT_TYPE")

-   [PROC\_DIST\_TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND.html#CP2K_INPUT.MOTION.BAND.PROC_DIST_TYPE "CP2K_INPUT.MOTION.BAND.PROC_DIST_TYPE")

-   [ROTATE\_FRAMES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND.html#CP2K_INPUT.MOTION.BAND.ROTATE_FRAMES "CP2K_INPUT.MOTION.BAND.ROTATE_FRAMES")

-   [USE\_COLVARS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/BAND.html#CP2K_INPUT.MOTION.BAND.USE_COLVARS "CP2K_INPUT.MOTION.BAND.USE_COLVARS")


## Keyword descriptions

### ALIGN\_FRAMES*: logical* *\= T*

**Lone keyword:** `T`

Enables the alignment of the frames at the beginning of a BAND calculation. This keyword does not affect the rotation of the replicas during a BAND calculation. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_neb.F#L153)\]

### BAND\_TYPE*: enum* *\= IT-NEB*

**Usage:** *BAND\_TYPE (B-NEB|IT-NEB|CI-NEB|D-NEB|SM|EB)*

**Valid values:**

-   `B-NEB` Bisection nudged elastic band

-   `IT-NEB` Improved tangent nudged elastic band

-   `CI-NEB` Climbing image nudged elastic band

-   `D-NEB` Doubly nudged elastic band

-   `SM` String Method

-   `EB` Elastic band (Hamiltonian formulation)


Specifies the type of BAND calculation \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_neb.F#L91)\]

### K\_SPRING*: real* *\= 2.00000000E-002*

**Aliases:** K

Specify the value of the spring constant \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_neb.F#L160)\]

### NPROC\_REP*: integer* *\= 1*

Specify the number of processors to be used per replica environment (for parallel runs) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_neb.F#L72)\]

### NUMBER\_OF\_REPLICA*: integer* *\= 10*

Specify the number of Replica to use in the BAND. This may be equal to or larger than the number of defined &REPLICA sections. If larger, the rest of missing replica will automatically be interpolated in an iterative bisection procedure: on each step, the largest distance between adjacent replica is found and a new replica is inserted there by taking the average of adjacent replica; this is repeated until getting requested number of replica. Please note that the number of replica is always including both end points regardless of the setting of keyword OPTIMIZE\_END\_POINTS, which should be taken into account when adjusting the NPROC\_REP value based on processors available on the machine. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_neb.F#L111)\]

### POT\_TYPE*: enum* *\= FULL*

**Usage:** *POT\_TYPE (FULL|FE|ME)*

**Valid values:**

-   `FULL` Full potential (no projections in a subspace of colvars)

-   `FE` Free energy (requires a projections in a subspace of colvars)

-   `ME` Minimum energy (requires a projections in a subspace of colvars)


Specifies the type of potential used in the BAND calculation \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_neb.F#L132)\]

### PROC\_DIST\_TYPE*: enum* *\= BLOCKED*

**Usage:** *PROC\_DIST\_TYPE (INTERLEAVED|BLOCKED)*

**Valid values:**

-   `INTERLEAVED` Interleaved distribution

-   `BLOCKED` Blocked distribution


Specify the topology of the mapping of processors into replicas. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_neb.F#L79)\]

### ROTATE\_FRAMES*: logical* *\= T*

**Lone keyword:** `T`

Compute at each BAND step the RMSD and rotate the frames in order to minimize it. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_neb.F#L146)\]

### USE\_COLVARS*: logical* *\= F*

**Lone keyword:** `T`

Uses a version of the band scheme projected in a subspace of colvars. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_neb.F#L126)\]
