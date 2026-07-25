# CP2K official manual snapshot: topology

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html
- Raw SHA-256: fc94acc8e2b30700568629fa68037989e86e0138a5929cc454a806393c1bc481
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# TOPOLOGY

Section specifying information regarding how to handle the topology for classical runs. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1654)\]

Subsections

-   [CENTER\_COORDINATES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY/CENTER_COORDINATES.html)
-   [DUMP\_PDB](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY/DUMP_PDB.html)
-   [DUMP\_PSF](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY/DUMP_PSF.html)
-   [EXCLUDE\_EI\_LIST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY/EXCLUDE_EI_LIST.html)
-   [EXCLUDE\_VDW\_LIST](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY/EXCLUDE_VDW_LIST.html)
-   [FRAGMENTS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY/FRAGMENTS.html)
-   [GENERATE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY/GENERATE.html)
-   [MOL\_SET](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY/MOL_SET.html)

## Keywords

-   [AUTOGEN\_EXCLUDE\_LISTS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.AUTOGEN_EXCLUDE_LISTS "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.AUTOGEN_EXCLUDE_LISTS")

-   [CHARGE\_BETA](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.CHARGE_BETA "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.CHARGE_BETA")

-   [CHARGE\_EXTENDED](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.CHARGE_EXTENDED "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.CHARGE_EXTENDED")

-   [CHARGE\_OCCUP](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.CHARGE_OCCUP "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.CHARGE_OCCUP")

-   [CONN\_FILE\_FORMAT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.CONN_FILE_FORMAT "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.CONN_FILE_FORMAT")

-   **[CONN\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.CONN_FILE_NAME "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.CONN_FILE_NAME")**

-   [COORD\_FILE\_FORMAT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.COORD_FILE_FORMAT "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.COORD_FILE_FORMAT")

-   [COORD\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.COORD_FILE_NAME "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.COORD_FILE_NAME")

-   [DISABLE\_EXCLUSION\_LISTS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.DISABLE_EXCLUSION_LISTS "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.DISABLE_EXCLUSION_LISTS")

-   [EXCLUDE\_EI](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.EXCLUDE_EI "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.EXCLUDE_EI")

-   [EXCLUDE\_VDW](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.EXCLUDE_VDW "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.EXCLUDE_VDW")

-   [MEMORY\_PROGRESSION\_FACTOR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.MEMORY_PROGRESSION_FACTOR "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.MEMORY_PROGRESSION_FACTOR")

-   [MOL\_CHECK](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.MOL_CHECK "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.MOL_CHECK")

-   [MULTIPLE\_UNIT\_CELL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.MULTIPLE_UNIT_CELL "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.MULTIPLE_UNIT_CELL")

-   [NUMBER\_OF\_ATOMS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.NUMBER_OF_ATOMS "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.NUMBER_OF_ATOMS")

-   [PARA\_RES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.PARA_RES "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.PARA_RES")

-   [USE\_ELEMENT\_AS\_KIND](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.USE_ELEMENT_AS_KIND "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.USE_ELEMENT_AS_KIND")

-   [USE\_G96\_VELOCITY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html#CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.USE_G96_VELOCITY "CP2K_INPUT.FORCE_EVAL.SUBSYS.TOPOLOGY.USE_G96_VELOCITY")


## Keyword descriptions

### AUTOGEN\_EXCLUDE\_LISTS*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *AUTOGEN\_EXCLUDE\_LISTS logical*

When True, the exclude lists are solely based on the bond data in the topology. The (minimal) number of bonds between two atoms is used to determine if the atom pair is added to an exclusion list. When False, 1-2 exclusion is based on bonds in the topology, 1-3 exclusion is based on bonds and bends in the topology, 1-4 exclusion is based on bonds, bends and dihedrals in the topology. This implies that a missing dihedral in the topology will cause the corresponding 1-4 pair not to be in the exclusion list, in case 1-4 exclusion is requested for VDW or EI interactions. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1785)\]

### CHARGE\_BETA*: logical* *\= F*

**Aliases:** CHARGE\_B

**Lone keyword:** `T`

**Usage:** *CHARGE\_BETA logical*

Read MM charges from the BETA field of PDB file. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1677)\]

### CHARGE\_EXTENDED*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *CHARGE\_EXTENDED logical*

Read MM charges from the very last field of PDB file (starting from column 81). No limitations of number of digits. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1685)\]

### CHARGE\_OCCUP*: logical* *\= F*

**Aliases:** CHARGE\_O

**Lone keyword:** `T`

**Usage:** *CHARGE\_OCCUP logical*

Read MM charges from the OCCUP field of PDB file. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1669)\]

### CONN\_FILE\_FORMAT*: enum* *\= GENERATE*

**Aliases:** CONNECTIVITY

**Usage:** *CONN\_FILE\_FORMAT (PSF|UPSF|MOL\_SET|GENERATE|OFF|G87|G96|AMBER|USER)*

**Valid values:**

-   `PSF` Use a PSF file to determine the connectivity. (support standard CHARMM/XPLOR and EXT CHARMM)

-   `UPSF` Read a PSF file in an unformatted way (useful for not so standard PSF).

-   `MOL_SET` Use multiple PSF (for now…) files to generate the whole system.

-   `GENERATE` Use a simple distance criteria. (Look at keyword BONDPARM)

-   `OFF` Do not generate molecules. (e.g. for QS or ill defined systems)

-   `G87` Use GROMOS G87 topology file.

-   `G96` Use GROMOS G96 topology file.

-   `AMBER` Use AMBER topology file for reading connectivity (compatible starting from AMBER V.7)

-   `USER` Allows the definition of molecules and residues based on the 5th and 6th column of the COORD section. This option can be handy for the definition of molecules with QS or to save memory in the case of very large systems (use PARA\_RES off).


Ways to determine and generate a molecules. Default is to use GENERATE \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2322)\]

### CONN\_FILE\_NAME*: string*

**Aliases:** CONN\_FILE

**Usage:** *CONN\_FILE\_NAME*

**Mentions:** ⭐[QM/MM with Built-in Force Field](https://manual.cp2k.org/cp2k-2026_2-branch/methods/qm_mm/builtin.html)

Specifies the filename that contains the molecular connectivity. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L2315)\]

### COORD\_FILE\_FORMAT*: enum* *\= OFF*

**Aliases:** COORDINATE

**Usage:** *COORD\_FILE\_FORMAT (OFF|PDB|XYZ|G96|CRD|CIF|XTL|CP2K)*

**Valid values:**

-   `OFF` Coordinates read in the &COORD section of the input file

-   `PDB` Coordinates provided through a PDB file format

-   `XYZ` Coordinates provided through an XYZ file format

-   `G96` Coordinates provided through a GROMOS96 file format

-   `CRD` Coordinates provided through an AMBER file format

-   `CIF` Coordinates provided through a CIF (Crystallographic Information File) file format

-   `XTL` Coordinates provided through a XTL (MSI native) file format

-   `CP2K` Read the coordinates in CP2K &COORD section format from an external file. NOTE: This file will be overwritten with the latest coordinates.


Set up the way in which coordinates will be read. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1725)\]

### COORD\_FILE\_NAME*: string*

**Aliases:** COORD\_FILE

**Usage:** *COORD\_FILE\_NAME*

Specifies the filename that contains coordinates. In case the CELL section is not set explicitly but this file contains cell information, including CIF, PDB and (Extended) XYZ formats, this file is also parsed for setting up the simulation cell. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1715)\]

### DISABLE\_EXCLUSION\_LISTS*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *DISABLE\_EXCLUSION\_LISTS*

Do not build any exclusion lists. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1760)\]

### EXCLUDE\_EI*: enum* *\= 1-3*

**Usage:** *EXCLUDE\_EI (1-1||1-2||1-3||1-4)*

**Valid values:**

-   `1-1`

-   `1-2`

-   `1-3`

-   `1-4`


Specifies which kind of Electrostatic interaction to skip. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1776)\]

### EXCLUDE\_VDW*: enum* *\= 1-3*

**Usage:** *EXCLUDE\_VDW (1-1||1-2||1-3||1-4)*

**Valid values:**

-   `1-1`

-   `1-2`

-   `1-3`

-   `1-4`


Specifies which kind of Van der Waals interaction to skip. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1767)\]

### MEMORY\_PROGRESSION\_FACTOR*: real* *\= 1.20000000E+000*

This keyword is quite technical and should normally not be changed by the user. It affects the memory allocation during the construction of the topology. It does NOT affect the memory used once the topology is built. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1813)\]

### MOL\_CHECK*: logical* *\= T*

**Lone keyword:** `T`

**Usage:** *MOL\_CHECK logical*

Check molecules have the same number of atom and names. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1700)\]

### MULTIPLE\_UNIT\_CELL*: integer\[3\]* *\= 1 1 1*

**Usage:** *MULTIPLE\_UNIT\_CELL 1 1 1*

Specifies the numbers of repetition in space (X, Y, Z) of the defined cell, assuming it as a unit cell. This keyword affects only the coordinates specification. The same keyword in SUBSYS%CELL%MULTIPLE\_UNIT\_CELL should be modified in order to affect the cell specification. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1804)\]

### NUMBER\_OF\_ATOMS*: integer* *\= \-1*

**Aliases:** NATOMS ,NATOM

**Usage:** *NATOMS 768000*

Optionally define the number of atoms read from an external file (see COORD\_FILE\_NAME) if the COORD\_FILE\_FORMAT CP2K is used \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1746)\]

### PARA\_RES*: logical* *\= T*

**Lone keyword:** `T`

**Usage:** *PARA\_RES logical*

For a protein, each residue is now considered a molecule \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1693)\]

### USE\_ELEMENT\_AS\_KIND*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *USE\_ELEMENT\_AS\_KIND logical*

Kinds are generated according to the element name. Default=True for SE and TB methods. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1661)\]

### USE\_G96\_VELOCITY*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *USE\_G96\_VELOCITY logical*

Use the velocities in the G96 coordinate files as the starting velocity \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_subsys.F#L1707)\]
