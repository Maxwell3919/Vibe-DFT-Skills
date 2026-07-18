# CP2K official manual snapshot: topology

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/TOPOLOGY.html
- Raw SHA-256: fc94acc8e2b30700568629fa68037989e86e0138a5929cc454a806393c1bc481
- Status: version-matched cached official text; reopen the source for current live verification.

TOPOLOGY



Section specifying information regarding how to handle the topology for classical runs.

[

Edit on GitHub

]

Subsections

CENTER_COORDINATES

DUMP_PDB

DUMP_PSF

EXCLUDE_EI_LIST

EXCLUDE_VDW_LIST

FRAGMENTS

GENERATE

MOL_SET

Keywords



AUTOGEN_EXCLUDE_LISTS

CHARGE_BETA

CHARGE_EXTENDED

CHARGE_OCCUP

CONN_FILE_FORMAT

CONN_FILE_NAME

COORD_FILE_FORMAT

COORD_FILE_NAME

DISABLE_EXCLUSION_LISTS

EXCLUDE_EI

EXCLUDE_VDW

MEMORY_PROGRESSION_FACTOR

MOL_CHECK

MULTIPLE_UNIT_CELL

NUMBER_OF_ATOMS

PARA_RES

USE_ELEMENT_AS_KIND

USE_G96_VELOCITY

Keyword descriptions



AUTOGEN_EXCLUDE_LISTS

:

logical

=

F



Lone keyword:

T

Usage:

AUTOGEN_EXCLUDE_LISTS logical

When True, the exclude lists are solely based on the bond data in the topology. The (minimal) number of bonds between two atoms is used to determine if the atom pair is added to an exclusion list. When False, 1-2 exclusion is based on bonds in the topology, 1-3 exclusion is based on bonds and bends in the topology, 1-4 exclusion is based on bonds, bends and dihedrals in the topology. This implies that a missing dihedral in the topology will cause the corresponding 1-4 pair not to be in the exclusion list, in case 1-4 exclusion is requested for VDW or EI interactions.

[

Edit on GitHub

]

CHARGE_BETA

:

logical

=

F



Aliases:

CHARGE_B

Lone keyword:

T

Usage:

CHARGE_BETA logical

Read MM charges from the BETA field of PDB file.

[

Edit on GitHub

]

CHARGE_EXTENDED

:

logical

=

F



Lone keyword:

T

Usage:

CHARGE_EXTENDED logical

Read MM charges from the very last field of PDB file (starting from column 81). No limitations of number of digits.

[

Edit on GitHub

]

CHARGE_OCCUP

:

logical

=

F



Aliases:

CHARGE_O

Lone keyword:

T

Usage:

CHARGE_OCCUP logical

Read MM charges from the OCCUP field of PDB file.

[

Edit on GitHub

]

CONN_FILE_FORMAT

:

enum

=

GENERATE



Aliases:

CONNECTIVITY

Usage:

CONN_FILE_FORMAT (PSF|UPSF|MOL_SET|GENERATE|OFF|G87|G96|AMBER|USER)

Valid values:

PSF

Use a PSF file to determine the connectivity. (support standard CHARMM/XPLOR and EXT CHARMM)

UPSF

Read a PSF file in an unformatted way (useful for not so standard PSF).

MOL_SET

Use multiple PSF (for now…) files to generate the whole system.

GENERATE

Use a simple distance criteria. (Look at keyword BONDPARM)

OFF

Do not generate molecules. (e.g. for QS or ill defined systems)

G87

Use GROMOS G87 topology file.

G96

Use GROMOS G96 topology file.

AMBER

Use AMBER topology file for reading connectivity (compatible starting from AMBER V.7)

USER

Allows the definition of molecules and residues based on the 5th and 6th column of the COORD section. This option can be handy for the definition of molecules with QS or to save memory in the case of very large systems (use PARA_RES off).

Ways to determine and generate a molecules. Default is to use GENERATE

[

Edit on GitHub

]

CONN_FILE_NAME

:

string



Aliases:

CONN_FILE

Usage:

CONN_FILE_NAME

Mentions:

⭐

QM/MM with Built-in Force Field

Specifies the filename that contains the molecular connectivity.

[

Edit on GitHub

]

COORD_FILE_FORMAT

:

enum

=

OFF



Aliases:

COORDINATE

Usage:

COORD_FILE_FORMAT (OFF|PDB|XYZ|G96|CRD|CIF|XTL|CP2K)

Valid values:

OFF

Coordinates read in the &COORD section of the input file

PDB

Coordinates provided through a PDB file format

XYZ

Coordinates provided through an XYZ file format

G96

Coordinates provided through a GROMOS96 file format

CRD

Coordinates provided through an AMBER file format

CIF

Coordinates provided through a CIF (Crystallographic Information File) file format

XTL

Coordinates provided through a XTL (MSI native) file format

CP2K

Read the coordinates in CP2K &COORD section format from an external file. NOTE: This file will be overwritten with the latest coordinates.

Set up the way in which coordinates will be read.

[

Edit on GitHub

]

COORD_FILE_NAME

:

string



Aliases:

COORD_FILE

Usage:

COORD_FILE_NAME

Specifies the filename that contains coordinates. In case the CELL section is not set explicitly but this file contains cell information, including CIF, PDB and (Extended) XYZ formats, this file is also parsed for setting up the simulation cell.

[

Edit on GitHub

]

DISABLE_EXCLUSION_LISTS

:

logical

=

F



Lone keyword:

T

Usage:

DISABLE_EXCLUSION_LISTS

Do not build any exclusion lists.

[

Edit on GitHub

]

EXCLUDE_EI

:

enum

=

1-3



Usage:

EXCLUDE_EI (1-1||1-2||1-3||1-4)

Valid values:

1-1

1-2

1-3

1-4

Specifies which kind of Electrostatic interaction to skip.

[

Edit on GitHub

]

EXCLUDE_VDW

:

enum

=

1-3



Usage:

EXCLUDE_VDW (1-1||1-2||1-3||1-4)

Valid values:

1-1

1-2

1-3

1-4

Specifies which kind of Van der Waals interaction to skip.

[

Edit on GitHub

]

MEMORY_PROGRESSION_FACTOR

:

real

=

1.20000000E+000



This keyword is quite technical and should normally not be changed by the user. It affects the memory allocation during the construction of the topology. It does NOT affect the memory used once the topology is built.

[

Edit on GitHub

]

MOL_CHECK

:

logical

=

T



Lone keyword:

T

Usage:

MOL_CHECK logical

Check molecules have the same number of atom and names.

[

Edit on GitHub

]

MULTIPLE_UNIT_CELL

:

integer

[

3

]

=

1



Usage:

MULTIPLE_UNIT_CELL 1 1 1

Specifies the numbers of repetition in space (X, Y, Z) of the defined cell, assuming it as a unit cell. This keyword affects only the coordinates specification. The same keyword in SUBSYS%CELL%MULTIPLE_UNIT_CELL should be modified in order to affect the cell specification.

[

Edit on GitHub

]

NUMBER_OF_ATOMS

:

integer

=

-1



Aliases:

NATOMS ,NATOM

Usage:

NATOMS 768000

Optionally define the number of atoms read from an external file (see COORD_FILE_NAME) if the COORD_FILE_FORMAT CP2K is used

[

Edit on GitHub

]

PARA_RES

:

logical

=

T



Lone keyword:

T

Usage:

PARA_RES logical

For a protein, each residue is now considered a molecule

[

Edit on GitHub

]

USE_ELEMENT_AS_KIND

:

logical

=

F



Lone keyword:

T

Usage:

USE_ELEMENT_AS_KIND logical

Kinds are generated according to the element name. Default=True for SE and TB methods.

[

Edit on GitHub

]

USE_G96_VELOCITY

:

logical

=

F



Lone keyword:

T

Usage:

USE_G96_VELOCITY logical

Use the velocities in the G96 coordinate files as the starting velocity

[

Edit on GitHub

]
