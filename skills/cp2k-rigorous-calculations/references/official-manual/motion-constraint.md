# CP2K official manual snapshot: motion-constraint

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT.html
- Raw SHA-256: 9b4559470ae890642b072e8b49f40f876e52d3d3a536c0c1f8115cf8b14be30b
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# CONSTRAINT

Section specifying information regarding how to impose constraints on the system. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_constraints.F#L67)\]

Subsections

-   [COLLECTIVE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT/COLLECTIVE.html)
-   [COLVAR\_RESTART](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT/COLVAR_RESTART.html)
-   [CONSTRAINT\_INFO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT/CONSTRAINT_INFO.html)
-   [FIXED\_ATOMS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT/FIXED_ATOMS.html)
-   [FIX\_ATOM\_RESTART](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT/FIX_ATOM_RESTART.html)
-   [G3X3](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT/G3X3.html)
-   [G4X6](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT/G4X6.html)
-   [HBONDS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT/HBONDS.html)
-   [LAGRANGE\_MULTIPLIERS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT/LAGRANGE_MULTIPLIERS.html)
-   [VIRTUAL\_SITE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT/VIRTUAL_SITE.html)

## Keywords

-   [CONSTRAINT\_INIT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT.html#CP2K_INPUT.MOTION.CONSTRAINT.CONSTRAINT_INIT "CP2K_INPUT.MOTION.CONSTRAINT.CONSTRAINT_INIT")

-   [PIMD\_BEADWISE\_CONSTRAINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT.html#CP2K_INPUT.MOTION.CONSTRAINT.PIMD_BEADWISE_CONSTRAINT "CP2K_INPUT.MOTION.CONSTRAINT.PIMD_BEADWISE_CONSTRAINT")

-   [ROLL\_TOLERANCE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT.html#CP2K_INPUT.MOTION.CONSTRAINT.ROLL_TOLERANCE "CP2K_INPUT.MOTION.CONSTRAINT.ROLL_TOLERANCE")

-   [SHAKE\_TOLERANCE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/CONSTRAINT.html#CP2K_INPUT.MOTION.CONSTRAINT.SHAKE_TOLERANCE "CP2K_INPUT.MOTION.CONSTRAINT.SHAKE_TOLERANCE")


## Keyword descriptions

### CONSTRAINT\_INIT*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *CONSTRAINT\_INIT*

Apply constraints to the initial position and velocities. Default is to apply constraints only after the first MD step. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_constraints.F#L89)\]

### PIMD\_BEADWISE\_CONSTRAINT*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *PIMD\_BEADWISE\_CONSTRAINT*

Apply beadwise constraints to PIMD. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_constraints.F#L97)\]

### ROLL\_TOLERANCE*: real* *\= 1.00000000E-010 \[internal\_cp2k\]*

**Aliases:** ROLL\_TOL ,ROLL

**Usage:** *ROLL\_TOLERANCE*

Set the tolerance for the roll constraint algorithm. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_constraints.F#L81)\]

### SHAKE\_TOLERANCE*: real* *\= 1.00000000E-006 \[internal\_cp2k\]*

**Aliases:** SHAKE\_TOL ,SHAKE

**Usage:** *SHAKE\_TOLERANCE*

Set the tolerance for the shake/rattle constraint algorithm. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_constraints.F#L73)\]
