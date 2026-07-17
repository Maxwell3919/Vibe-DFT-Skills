# INPUT_PH — NAMELIST: &INPUTPH — Item: electron_phonon

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `d3011609b69816059bb36a5ae99c72fffa8b0f4eee84fe4c767044c48e29d5cf`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


electron_phonon

CHARACTER

Default:

' '

Options are:

'simple'
:

Electron-phonon lambda coefficients are computed
for a given q and a grid of k-points specified by
the variables 
nk1
, 
nk2
, 
nk3
, 
k1
, 
k2
, 
k3
.

'interpolated'
:

Electron-phonon is calculated by interpolation
over the Brillouin Zone as in M. Wierzbowska, et
al. 
arXiv:cond-mat/0504077

'lambda_tetra'
:

The electron-phonon coefficient \lambda_{q \nu}
is calculated with the optimized tetrahedron method.

'gamma_tetra'
:

The phonon linewidth \gamma_{q \nu} is calculated
from the electron-phonon interactions
using the optimized tetrahedron method.

'epa'
:

Electron-phonon coupling matrix elements are written
to file prefix.epa.k for further processing by program
epa.x which implements electron-phonon averaged (EPA)
approximation as described in G. Samsonidze & B. Kozinsky,
Adv. Energy Mater. 2018, 1800246 
doi:10.1002/aenm.201800246

arXiv:1511.08115

'ahc'
:

Quantities required for the calculation of phonon-induced
electron self-energy are computed and written to the directory

ahc_dir
. The output files can be read by postahc.x for
the calculation of electron self-energy.
Available for both metals and insulators.

trans
=.false. is required.

For metals only, requires gaussian smearing (except for 'ahc').

If 
trans
=.true., the lambdas are calculated in the same
run, using the same k-point grid for phonons and lambdas.
If 
trans
=.false., the lambdas are calculated using
previously saved DeltaVscf in 
fildvscf
, previously saved
dynamical matrix, and the present punch file. This allows
the use of a different (larger) k-point grid.

[
Back to Top
]
```
