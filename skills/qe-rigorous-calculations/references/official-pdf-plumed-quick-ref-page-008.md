# plumed_quick_ref.pdf — page 8

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/plumed_quick_ref.pdf
- Retrieved: 2026-07-17T11:53:37+00:00
- Official source SHA-256: `a5c2a829e53a280183e491dba76248bb2cf4be7a775fb97ab03e8f86af15b09f`
- Extracted text SHA-256: `b69c31ba38d9b143316e2d8c86ad8aebed902c83eab7ac84bbc1d1f2bad34d39`
- Official Last-Modified: Mon, 08 Dec 2025 21:59:52 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
     Here we describe briefly the syntax used in the PLUMED input file. For the detail
introduction, please have a look at the PLUMED manual[5].
     The symbol # allows the user to comment any line in the input file. The HILLS
turns on the standard Metadynamics and the HEIGHT 0.001 means the height of the
Gaussians is 0.001 Rdy. Pay attention: in this code distances are in Bohr (1 Bohr =
0.529177249 Å) and the energies in Rydberg (1 Rydberg = 13.60569 eV). The frequency
for add Gaussians is controlled by W STRIDE followed by a number that represents the
number of steps between one MD step and the other which is 2 here. The line that starts
with the keyword PRINT W STRIDE control the frequency for the main PLUMED output
file which is called COLVAR. This file contains the data regarding the collective variable
positions, the constraint positions, the energy of hills and energy of constraints and
other useful informations that will be introduced time by time during the tutorial. All
the informations are appended in the COLVAR file and overwritten if an old COLVAR file
already exists. The DISTANCE LIST 1 3 shows that our CV1 is the distance between
atom 1 and atom 3, the SIGMA 0.3 indicates the width of the Gaussians is 0.3 Bohr. In
order to prevent to depart the two molecules, we add the wall potentials on CV1 and
CV2, for both of them the upper limit wall and the lower limit wall. The UWALL and
LWALL keywords define a wall for the value of the CV s which limits the region of the
phase space accessible during the simulation. The restraining potential starts acting
on the system when the value of the CV is greater (in the case of UWALL) or lower (in
the case of LWALL) than a certain limit LIMIT. The functional form of this potential is
the following:
                                           s − LIM IT + OF F EXP
                    Vwall (s) = KAP P A(                    )                     (5)
                                                 EP S
    where KAPPA is an energy constant in internal unit of the code, EPS a rescaling
factor and EXP the exponent determining the power law. By default: EXP = 4, EPS =
1.0, OFF = 0.
    The termination of the input for PLUMED is marked with the keyword ENDMETA.
Whatever it follows is ignored by PLUMED. You can introduce blank lines. They are not
interpreted by PLUMED.
    Here is the input file pw.in for pw.x:

 &control
    title = ’ch3cl’,
    calculation=’md’
    restart_mode=’from_scratch’,
    pseudo_dir = ’./’,
    outdir = ’./tmp’,
    dt=20,
    nstep=2000,
    prefix = ’md’,
 /
 &system
    ibrav = 8,
    celldm(1) = 18.d0,


                                            8
```
