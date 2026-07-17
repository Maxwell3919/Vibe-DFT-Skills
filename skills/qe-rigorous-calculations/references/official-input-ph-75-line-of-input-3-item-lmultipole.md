# INPUT_PH — LINE OF INPUT — Item: lmultipole

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `1cd8371994760fe1ee9d9256bd5fb236bc3c9483ab35c07a0193f739deed6ebd`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


lmultipole

LOGICAL

Default:

.false.

If .true. prints the induced density and potentials in 
fildrho

and 
fildvscf
. To extract multipoles and the finite-q dielectric
function, multiple finite-q calculations need to be performed (see:
test-suite/ph_multipole, where multipole.py manages the flow of the
calculations as described in test-suite/run-ph.sh).
Works only for 3d systems.

[
Back to Top
]

ADDITIONAL INFORMATION 

NB: The program ph.x writes on the tmp_dir/_ph0/{prefix}.phsave directory
a file for each representation of each q point. This file is called
dynmat.#iq.#irr.xml where #iq is the number of the q point and #irr
is the number of the representation. These files contain the
contribution to the dynamical matrix of the irr representation for the
iq point.

If 
recover
=.true. ph.x does not recalculate the
representations already saved in the tmp_dir/_ph0/{prefix}.phsave
directory. Moreover ph.x writes on the files patterns.#iq.xml in the
tmp_dir/_ph0/{prefix}.phsave directory the displacement patterns that it
is using. If 
recover
=.true. ph.x does not recalculate the
displacement patterns found in the tmp_dir/_ph0/{prefix}.phsave directory.

This mechanism allows:

1) To recover part of the ph.x calculation even if the recover file
or files are corrupted. You just remove the _ph0/{prefix}.recover
files from the tmp_dir directory. You can also remove all the _ph0
files and keep only the _ph0/{prefix}.phsave directory.

2) To split a phonon calculation into several jobs for different
machines (or set of nodes). Each machine calculates a subset of
the representations and saves its dynmat.#iq.#irr.xml files on
its tmp_dir/_ph0/{prefix}.phsave directory. Then you collect all the
dynmat.#iq.#irr.xml files in one directory and run ph.x to
collect all the dynamical matrices and diagonalize them.

NB: To split the q points in different machines, use the input
variables start_q and last_q. To split the irreducible
representations, use the input variables 
start_irr
, 
last_irr
. Please
note that different machines will use, in general, different
displacement patterns and it is not possible to recollect partial
dynamical matrices generated with different displacement patterns. A
calculation split into different machines will run as follows: A
preparatory run of ph.x with 
start_irr
=0, 
last_irr
=0 produces the sets
of displacement patterns and save them on the patterns.#iq.xml files.
These files are copied in all the tmp_dir/_ph0/{prefix}.phsave directories
of the machines where you plan to run ph.x. ph.x is run in different
machines with complementary sets of start_q, last_q, 
start_irr
and

last_irr
variables. All the files dynmat.#iq.#irr.xml are
collected on a single tmp_dir/_ph0/{prefix}.phsave directory (remember to
collect also dynmat.#iq.0.xml). A final run of ph.x in this
machine collects all the data contained in the files and diagonalizes
the dynamical matrices. This is done requesting a complete dispersion
calculation without using start_q, last_q, 
start_irr
, or 
last_irr
.
See an example in examples/GRID_example.

On parallel machines the q point and the irreps calculations can be split
automatically using the -nimage flag. See the phonon user guide for further
information.

This file has been created by helpdoc utility on Tue Oct 14 12:25:47 CEST 2025.
```
