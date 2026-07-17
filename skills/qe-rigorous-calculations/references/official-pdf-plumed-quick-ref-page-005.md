# plumed_quick_ref.pdf — page 5

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/plumed_quick_ref.pdf
- Retrieved: 2026-07-17T11:53:37+00:00
- Official source SHA-256: `a5c2a829e53a280183e491dba76248bb2cf4be7a775fb97ab03e8f86af15b09f`
- Extracted text SHA-256: `cdcb4758c65375c17a2e8fad14d954fdab12578953613e496e46532a9fd824ae`
- Official Last-Modified: Mon, 08 Dec 2025 21:59:52 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
cd espresso-X.Y.Z/
./configure
make plumed

2.2    Running metadynamics in Quantum ESPRESSO
To run the metadynamics calculations, you will need to prepare the input file plumed.dat
for PLUMED (see PLUMED manual[5] for a detailed description), that should be located in
outdir and the standard input file for Quantum ESPRESSO. And then, you may
execute the program as usual but with a flag -plumed.
    For Born-Oppenheimer Molecular Dynamics,

pw.x -plumed < pw.in > pw.out

   for Car-Parrinello Molecular Dynamics,

cp.x -plumed < cp.in > cp.out

2.3    Units in the input and output files
There are several output files for the simulation with PLUMED, e.g. PLUMED.OUT, COLVAR
and HILLS. All the units in the input and output files for PLUMED adopt the internal
units of the main code, say Rydberg atomic units in pw.x and Hartree atomic units in
cp.x. But there are two exceptions, for distance it is always Bohr and for energy it is
always Rydberg.

2.4    Postprocessing
There is a sum hills.f90 code (in espresso/PLUMED/utilities/sum hills/) perform-
ing post-processing task to estimate the free energy after a metadynamics run. The
program sum hills.f90 is a tool for summing up the Gaussians laid during the meta-
dynamics trajectory and obtaining the free energy surface.
   As sum hills.f90 is a simple fortran 90 program, the installation is straight- for-
ward so long as you have a fortran compiler available on your machine. As an example,
with the gnu g95 compiler one would compile sum hills.f90 using the following com-
mand:

g95 -O3 sum_hills.f90 serial.f90 -o sum_hills.x

    For post processing of large HILLS files it is recommended to use a parallel version.
    The sum hills.x program takes its input parameters from the command line. If
run without options, this brief summary of options is printed out. Detail descriptions
of the following options can be found in the manual[5] of PLUMED.

USAGE:
sum_hills.x -file HILLS -out fes.dat -ndim 3 -ndw 1 2 -kt 0.6 -ngrid 100 100 100
[-ndim 3         ] (number of collective variables NCV)

                                           5
```
