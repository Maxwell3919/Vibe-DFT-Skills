# CP2K official manual snapshot: changelog

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/changelog.html
- Raw SHA-256: f0c9f2f7da19302fda628ea291b918ba13ca6b9437f28f760425b76938e186b4
- Status: version-matched cached official text; reopen the source for current live verification.

Changelog



2026.2 (July 15, 2026)



New Features



DFT+U with k-points for Mulliken methods (

#4855

)

Energy Correction Harris functional with k-points

(

#5031

)

Lowdin population analysis for k-points (

#5045

)

Wavefunction extrapolation for k-point calculations

(

#4884

,

#4943

,

#4949

,

#5219

)

GExt wavefunction extrapolation (

#5043

,

#5229

)

Adaptively Compressed Exchange (ACE) option to the HFX/ADMM ground-state path

(

#5238

)

Alternative smearing methods (

#4958

)

Brownian chain molecular dynamics (BCMD) propagator for path integrals

(

#5247

)

DOS/PDOS with broadened output and k-point projections

(

#5287

,

#5299

,)

K-point symmetry reduction (

#5123

,

#5152

,

#5165

,

#5173

)

Input keyword for cutoff radius of HFX shortrange potential

(

#4945

)

Input keyword for L-BFGS optimizer print control (

#5274

)

New output of NEB including relative energy plot and final structures

(

#5382

)

New output of final structure from optimization in CIF and EXTXYZ formats

(

#5118

,

#5140

)

New output of Hessian before mass weighting from revised vibrational analysis printout

(

#5395

)

Dimer initialization by reading molden files (

#5312

)

Parse cell information from EXTXYZ for both initial geometry and each frame of reftraj run

(

#4960

,

#5401

)

Wrapping input atomic coordinates for each frame before calculation in a reftraj run

(

#5479

)

Per-thermal-region function for rescaling temperatures in MD (independent of thermostats)

(

#5002

)

Cell optimization with fixed volume (

#5086

)

New Libraries



Add openPMD output, including scientific metadata support

(

#4058

,

#4931

,

#4942

,

#5096

)

GauXC/Skala models (

#5084

)

LibFCI active-space solver (

#5167

)

Reintegrate with LIBXS, LIBXSTREAM, and LIBXSMM (

#5343

)

Add libGint for Hartree–Fock exchange with CUDA acceleration

(

#5446

)

Breaking Changes



Remove &MOTION/&CELL_OPT/TYPE; cell optimizations now always use DIRECT_CELL_OPT

(

#5257

)

Drop support for GCC 8 (

#5290

)

Refactor DOS/PDOS input section (

#5326

)

Remove obsolete Cython Python bindings (

#5541

)

Remove EVAL_ENERGY_FORCES and EVAL_FORCES keywords in favor of EVAL under &MOTION/&MD/&REFTRAJ

(

#5401

)

An implementation of the FFTW3 interface may be turned into a hard dependency in a later release.

Please consider compiling and CP2K with FFTW3, MKL, AOCL or any other library implementing this

interface if you have not used it until now. (

#5454

)

Fixes



Fix issues in the native DFT-D4 implementation. (

#5030

)

Analytical periodic-subspace stress for 2D systems with ANALYTIC/MT

(

#5282

)

2026.1 (January 6, 2026)



New Features



Add new BASIS_AUG_MOLOPT and BASIS_RI_AUG_MOLOPT basis sets (all electron)

(

#4354

)

Active Space: Added a new longrange truncated potential for the ERI

(

#4357

)

Activate handling of GTH-SOC PP in Sirius (

#4363

)

Better availability of occupied orbital eigenvalues from OT

(

#4364

)

CNEO-DFT energy and force (

#4403

,

#4420

)

Sternheimer BSE (1. Version with W matrix given) (

#4445

)

SF-TDDFT implementation (

#4446

)

PAO-ML: Migrate to NequIP framework (

#4461

)

GAPW DC-DFT + EC EXTERNAL (

#4502

)

NEGF: New method to extract the matrix Hamiltonians for electrodes

(

#4520

,

#4636

)

precommit: Add Fortitude linter (

#4523

)

RT-TDDFT+RT-BSE : Fourier Transform Outputs (

#4527

)

RIXS: Open-Shell (

#4533

)

Add interface to the MiMiC framework for multiscale simulations

(

#4546

)

Restricted Space Excitations for TDDFPT (

#4560

,

#4588

)

Vibronic spectroscopy post-processing tools (

#4581

)

Add extended XYZ format for trajectories (

#4601

)

Add MAX_FILE_SIZE_MB keyword to MO_CUBES section (

#4603

)

Implementation of moments for k-point calculations

(

#4621

)

Breaking Changes



Remove Makefile (

#4618

)

Remove QUIP (

#4616

)

Some remaining issues with Intel compilers and CMake

(

#4550

)

Fixes



Fix missing (zero) orbital eigenvalues in the MOLDEN output

(

#4364

)

Fix gradient for peridic systems with tblite(

#4397

)

Fix stress tensor in tblite (

#4406

)

Fix force constant in vibrational analysis (

#4427

)

Fix molecule indexing when using MULTIPLE_UNIT_CELL

(

#4437

)

Fix HFX initialization performance issue (

#4455

)

Fix 3PNT linesearch for CG in GEO_OPT (

#4665

)

2025.2 (July 23, 2025)



New Features



TDDFPT: Add exciton descriptors (

#3847

)

Efield implementation for xTB (

#3883

)

Atom code: Add option to write xmgrace wavefunction file

(

#3962

)

GFN-xTB (

#4005

,

#4190

,

#4209

,

#4242

)

Read/write external energy derivatives from/to trexio files

(

#4009

,

#4074

)

Pseudopotentials: Add 5f-in-core for trivalent and tetravalent actinides

(

#4068

)

Pseudopotentials: Add ccECP (

#3940

)

RTBSE : Padé FT Refinement (

#4115

)

HP-DFT modules and regtests (

#4138

)

Add option to print space groups (

#4271

)

Add SIRIUS DFTD3 and DFTD4 support (

#4277

)

Atomic polarization tensors via numerical differentiation

(

#4287

)

RI-HFXk: Various improvements (

#4291

)

Resonant Inelastic X-ray Spectroscopy (RIXS) Module

(

#4315

)

New Libraries



Improve DLA-Future integration (

#4169

,

#4269

)

Upgrade to DeePMD 3.1.0 and switch to PyTorch backend

(

#3893

,

#4310

)

Make GRPP an internal dependency (

#3966

)

Interface for greenX library (

#4078

)

Add ace support (

#4182

)

Breaking Changes



Remove old TDDFPT code (

#4066

)

Restore old format for writing forces to .xyz files

(

#4294

)

RTBSE: Input structure changed (

#3918

)

Fixes



Fix occurrence of ghost states with SVDs (

#3911

)

Speedup loading of NequIP and Allegro models (

#3912

)

TDDFPT%MGRID bug fix for GAPW (

#3967

)

Fix typo in data/BASIS_ccGRB_UZH (

#4017

)

2025.1 (January 1, 2025)



New Features



BSE: Optical spectra, BSE@evGW(0), and lots more (

#3628

,

#3659

,

#3781

,

#3793

,

#3815

)

Real time Bethe-Salpeter Propagation (

#3691

)

Harris and EHT methods incl. LS solver (

#3665

,

#3780

,

#3790

)

Print wannier states coefficients in AO basis (

#3683

,

#3687

)

Add Z-matrix formalism and EVERY_N_STEP keyword for linear response

(

#3689

,

#3692

)

RPA based SIGMA Functionals (

#3695

)

Framework to calculate response forces for external energy expressions based on KS orbitals

(

#3721

)

PAO: Add prediction from equivariant PyTorch models

(

#3738

)

gfn0-xTB and parallel DFT-D4 (

#3765

,

#3679

,

#3685

)

Smeared occupation TDA (

#3829

)

GW: Add keywords SIZE_LATTICE_SUM and KPOINTS_W (

#3833

)

New Libraries



Add

SMEAGOL

for electron transport with NEGF

(

#3716

)

Add

cuSOLVERMp

generalized eigensolver (

#3787

)

Add

DLA-Future

generalized

and complex eigensolvers (

#3799

,

#3813

,

#3819

)

Add

TREXIO

file format writer

(

#3792

)

Breaking Changes



Weighting of RSMD colvar is modified for the case of subsystem = list

(

#3818

)

Fixes



Re-init FFT scratch in case of PW env changes (

#3661

)

Add asserts after malloc and realloc in DBM and grid code

(

#3706

)

Fix segmentation fault when performing CDFT-MD with many constraints

(

#3711

)

Fix thread-safety in fft_tools (

#3729

)

Fix access to unallocated arrays in pme, spme, and ewalds

(

#3733

)

Fix handling of empty file names in the input (

#3758

)

Fix bug in TDDFPT/Davidson restart (

#3821

)

Fix bug in RTP/EMD restart (

#3637

)

Add initialization step to i-Pi which some clients expect

(

#3747

)

2024.3 (September 9, 2024)



This is a minor release to fix an issue with the PW environment that can lead to stalls during MD

(https://github.com/cp2k/cp2k/issues/3661).

Since this only affects MPI jobs, the ssmp binaries from the previous

2024.2 release

are still up-to-date.

2024.2 (August 6, 2024)



New Features



Many new pages in the methods section of

the manual

ECP nuclear gradients (

#3210

)

New basis sets (

#3266

,

#3276

#3460

,

#3561

)

TDA Kernel methods (

#3273

)

Bethe Salpeter equation for molecules (

#3308

,

#3329

)

Stress prediction in NequIP & Allegro (

#3428

,

#3445

)

GW for small unit cells with full k-points (

#3448

,

#3505

,

#3513

)

Hedin shift for G0W0 (

#3533

)

i-PI server functionality (

#3420

)

Infrastructure for Kpoint symmetries (

#3482

)

New Libraries



Machine learning with the

DeePMD-kit

(

#3145

)

Dispersion correction with the

DFTD4 library

(

#3501

)

GPU support via OpenCL (

#3321

,

#3315

,

#3375

)

Breaking Changes



Increase ScaLAPACK default block size to 64 (

#3184

)

Remove

BROYDEN_MIXING_NEW

option (

#3346

)

Remove

KP_RI_EXTENSION_FACTOR"

keyword (

#3223

)

Mark support for QUIP and PEXSI as deprecated (

#3600

)

Fixes



Fix oscillator strength for TDDFT+SOC within length and velocity representation

(

#3201

)

External potential: Do not re-parse potential function at each grid-point

(

#3204

)

PWDFT: Print the band gap and total energy (

#3211

)

Fix bug

#3218

in screening of hfx derivatives

(

#3221

)

Fix bug

#3217

in printout of eigenvalues and

eigenvectors (

#3230

)

Improve element comparison in reftraj (

#3337

)

Allegro: Fix parallelization with virials (

#3445

)

FFTW: Fix import/export wisdom file (

#3492

,

#3496

)

2024.1 (January 3, 2024)



New Features



Docs: Launch Sphinx-based

manual

(

#2883

)

TDDFPT: Pseudopotentials, GAPW, GPW, and forces (

#2895

,

#2932

,

#2940

,

#3011

,

#3110

,

#3122

)

RI-HFX for K-points (with gradients and ADMM) (

#2998

)

ADMM: input short cuts (

#3118

)

Long-range quantum computing (WF) in short-range DFT embedding

(

#2924

)

Active space: Implement ERI calculation using half-transformed integrals

(

#3082

)

GW: open-shell periodic GW (

#2920

,

#3045

,

#3125

)

G0W0/SOC: bandstructure, PDOS, local bandgap, periodic

(

#2994

,

#3130

)

NNP: Helium-Solute for interaction (

#3043

)

Time-dependent Field for EMD (

#3081

)

New Libraries



Add experimental support for

DLA-Future

eigensolver

(

#3143

)

Enabling calculations with ECPs

libgrpp

library

(

#3147

)

Breaking Changes



Remove SINGLE_PRECISION_MATRICES keyword (

#3096

,

#3140

)

Abort run by default on SCF convergence failure (

#3148

)

Drop support for NDEBUG (

#3172

)

Production docker files moved to

new repository

(

#3083

)

MD: Refactor REFTRAJ / EVAL_ENERGY_FORCES keyword

(

#2981

)

Drop CMake option

CP2K_BUILD_DBCSR

(

#3044

)

Fixes



Correct LnPP2 Basis sets. Some typos corrected Jun-Bo Lu

(

#3100

,

#3102

)

Fix Wannier localization when using LOW SPIN ROKS

(

#3108

)

XAS_TDP: Fix bug leading to crashes when n_ranks>>>nex_atom

(

#2908

)

EMD + Time Dependent Electric Field (

#3016

)

Fix parsing atom sites from CIF files (

#3092

)

Fix parsing of CHARMM General Force Fields (

#2956

)

2023.2 (July 28, 2023)



GW: Periodic open-shell and Splitting of electronic states due to spin-orbit coupling

(

#2639

,

#2831

)

GTH pseudopotential database file with spin-orbit coupling (SOC) parameters added

(

#2848

)

RTP: TD Field Velocity gauge and projection TD-MOs

(

#2623

,

#2744

)

RTP: Linear density delta kick and restart (

#2543

)

RTP: Enabled ADMM with GAPW (

#2729

)

Implementation of the NVPT for APTs and AATs in velocity form

(

#2568

,

#2561

)

Intrinsic Atomic Orbitals (

#2707

)

Machine Learning: Add PyTorch interface, Nequip and Allegro models

(

#2420

,

#2528

,

#2722

)

k-points: Implementation of the DIIS/Diag. solver

(

#2721

)

TDDFPT: SOC absorption (

#2859

)

GAPW triplet excitation energies and forces (

#2837

,

#2861

)

EC: Enable DC-DFT with HFX-ADMM for reference and DC calculation

(

#2780

)

Add cell symmetry

HEXAGONAL_GAMMA_120

(

#2758

)

Grid: Rename backends, change default to

CPU

(

#2772

,

#2775

,

#2778

)

Grid: Enable GPU acceleration for large basis sets

(

#2787

,

#2793

)

FM: Add experimental support for

NVIDIA cuSOLVERMp

(

#2860

)

Regtesting: Add

--smoketest

option (

#2501

)

Add support for MPI Fortran 2008 bindings (

#2486

)

Add support for

Apptainer/Singularity

containers

(

README

)

2023.1 (January 1, 2023)



Add gradients for SOS-MP2 and RPA incl. benchmarks

(

#2208

,

#2271

,

#2473

)

TDDFT/Linear Response: Add GAPW/GAPW_XC and ADMM/GAPW options

(

#2200

)

TDDFT: Add excited state forces as property (

#2363

)

RI-RPA: Allow for XC correction in ADMM RI-RPA (

#2216

)

RTP: Velocity gauge and magnetic delta pulse (

#2343

)

GW: Automatically extrapolate k-point mesh (

#2229

)

xTB: Add vdW options (

#2431

)

xTB: Fix electronic energy dependence on EPS_DEFAULT

(

#2287

)

Vibrational analysis: Raman Intensities (

#2263

)

New pseudopotentials and basis sets (

#2472

,

#2193

)

Improve NewtonX interface (

#2443

)

Fist: Add LAMMPS style tabulated pair potentials

(

#2313

)

EC: Variational Density-Corrected DFT (DC-DFT) (

#2322

)

Update active space interface (

#2346

)

Helium: Add missing xyz output format (

#2432

)

SIRIUS: Add support for libvdwxc (

#2270

)

ELPA: Fix block size issue on GPU (

#2407

)

Drop Support for MPI 2.0 (

#2438

)

Add experimental CMake build system (

#2364

)

Fix regtests on ARM64 (

#1855

)

Start testing with Address Sanitizer (

#2306

)

Start testing on macOS Apple M1 (sponsored by

MacStadium

)

2022.2 (October 4, 2022)



Minor release to fix the outdated url for Spglib in the toolchain

(

#2262

).

2022.1 (July 8, 2022)



Migrate tensor operations to new sparse matrix library DBM

(

#1863

)

Add HIP support for PW (

#1864

)

Drop support for GCC 5 (

#1878

)

Add GAPW Voronoi integration (

#1919

)

Remove deprecated sections LIBXC and KE_LIBXC (

#1921

)

Add LibXC equivalents to ADMM exchange potentials

(

#1972

)

Improve support for metaGGA functionals (

#1974

)

Use SPLA for offloading dgemm on GPUs in the mp2 module

(

#1951

)

TDDFT: enable state following using transition charge finger print

(

#1991

)

Add barostat for frozen atoms in absolute coordinate

(

#2000

)

Fix linkage of COSMA (

#2021

)

Migrate to centralized

__OFFLOAD_CUDA/HIP

flags

(

#2027

)

Add low-scaling SOS-Laplace MP2 forces (

#2031

)

Refactoring of basis set optimization code (

#2068

)

Add k-points for the GW self-energy (

#2073

)

CDFT: forces based on Hirshfeld partitioning (

#2111

)

RPA: Add low-scaling gradients (

#2131

)

MP2: Add more solvers (

#2142

)

GW: Add 4-center Hartree-Fock and ADMM for exchange self-energy

(

#2145

)

Print vibrational modes for Newton-X (

#2146

)

Add partially occupied Wannier states (

#2154

)

Voronoi integration: Mitigated issues with symmetric structures, more diagnostic output

(

#2171

)

Add GAPW_XC for TDDFPT energies (

#2178

)

9.1 (December 31, 2021)



Fix MacOS build (

#1316

)

Add NEWTONX interface (

#1794

)

Add Gromacs QM/MM support

(

see also

)

Add experimental support for HIP and OpenCL to DBCSR

Adopt BSD3 license for new performance critical code

(

#1632

)

Add GAL21 forcefield (

#1579

)

Upgrade to MPI_THREAD_SERIALIZED (

#1564

)

Add new pseudopotentials and basis sets (

#1547

,

#1551

)

Add analytical derivatives of the MO coefficients wrt nuclear coordinates

(

#1706

)

Add forces for RI-HFX (

#1688

)

Add forces for TDDFT (

#1670

,

#1759

)

Regularized RI for periodic GW (

#1776

)

Add beadwise constraints to PINT (

#1734

)

Add analytical stress tensor for NNP (

#1783

)

Add ghost particles and tip scan for xTB (

#1578

)

Add forces and stress tensor for MP2-based double-hybrids

(

#1647

)

Rewrite regtesting script in Python, arguments changed slightly

(

#1548

)

8.2 (May 28, 2021)



Speedup grid kernels, especially non-orthorhombic on CPU and integrate on GPU

Upgrade to COSMA 2.5 (

#1303

)

Add support for ARM64

Drop support for GCC 6 (

#1203

)

Upgrade to LibXC 5 and

harmonize its input

with built in functionals

xTB/DFTB: Add stress tensor with efield

Motion: Add space group symmetry

Fix multi GPU by setting the active device consistently

(

#814

)

Fix MOLDEN output (

#1335

)

XAS_TDP: Fix bug in open-shell SOC (

#1304

)

PINT: Fix conserved quantity in PINT-RPMD restart

(

#1290

)

ELPA: As a precaution use only for large matrices by default

(

#1444

)

libvori

: Augmented .voronoi file format provides improved

support for

TRAVIS

(e.g. for spectra simulations)

8.1 (December 30, 2020)



Fix bug affecting ADMM on GPUs (

#893

)

Fix bug affecting Amber dihedrals (

#984

)

Drop support for Python 2 and non-OpenMP builds

Add interfaces to GRRM17 and SCINE codes

Add support for Cosma (https://github.com/eth-cscs/COSMA)

Add support for Voronoi integration of electron density (https://brehm-research.de/voronoi)

Add support for output of electron density in compressed BQB format

(https://brehm-research.de/bqb)

OpenMP refactoring and speed-ups for one electron integrals

Response code for polarizabilities: add finite difference debug, hybrid functionals, and ADMM

Harris functional based on Kohn-Sham density

TDDFPT code refactoring, add sTDA kernel, xTB/sTDA method

NNP: Behler-Parrinello Neural Network Potentials

XAS_TDP: Add OT solver and improve performance

mGGA: Add stress tensor and fix bug (

#1116

)

QMMM: Add benchmarks and speedup GEEP with OpenMP

LS: Add sign calculation based on submatrix method

ALMO: Add trust region methods

RI-HFX: Add resolution of identity for Hartree-Fock exchange

RPA/GW/MP2: Several optimizations and refactoring to low-scaling implementation

CUDA: GPU acceleration of collocate and integrate grid operations (experimental)

7.1 (December 24, 2019)



SIRIUS

: Plane Wave module with GPU support, see

also

this tutorial

for Quantum ESPRESSO

users.

xTB: Tight-binding module based on

RPA / GW / MP2: migrated to DBCSR tensors.

HELIUM: New canonical worm algorithm based on

.

XAS_TDP: X-ray absorption spectra simulations using linear-response TDDFT.

NEGF: Contact-specific temperature, correct shift and scale factors.

S-ALMO: Major refactoring, added wide variety of options.

CDFT: Cleanup and bug fixing.

FPGA interface for pw FFT.

Updated libraries: DBCSR, ELPA, libint, libxc, libxsmm.

The cp2k_shell was integrated into the main binary, simply call cp2k with

-s

or

--shell

.

Development moved from SVN to Git

6.1 (June 11, 2018)



Projection-operator adiabatization (POD) method

CP2K can now do Plane Wave calculations using CPU and GPU, based on an electronic structure

library

SIRIUS

Include NVIDIA P100 kernels for DBCSR

Update toolchain

Prevent ELPA diagonalization crashes with small matrices and/or large core counts

Faster routines for reading and writing cube files using MPI I/O

Docker based tests

5.1 (October 24, 2017)



Sparse tensor framework based on DBCSR

Flags

__ELPA2

and

__ELPA3

removed, instead use

-D__ELPA=YYYYMM

to specify library version.

Constrained DFT, see

CDFT

and

MIXED_CDFT

Cubic scaling GW

GW + image charge to compute electronic levels of a molecule on a metal surface

Constraint cell optimization

CP2K_INPUT.MOTION.CELL_OPT.CONSTRAINT

4.1 (October 5, 2016)



Maximum Overlap Method (MOM)

Modified Atomic Orbitals (MAO) Analysis

Easier installation with an improved

toolchain

Improved Development Tools:

prettifier

,

API documentation

Improved

Coding Standards

More collective variables

Transport with Omen:

improvements

libcp2k.h

interface (C/C++ header)

Remote Memory Access (RMA) for future architectures

Various performance improvements and bug fixes

GTH-PBE pseudopotentials for the Lanthanide elements

Polarized Atomic Orbitals from Machine Learning (PAO-ML)

Cubic-scaling RPA

Fast method for periodic ERI reducing overhead of image charge correction in QM/MM and used in

cubic-scaling RPA

Drop support for PLUMED 1.3 (PLUMED 2.x is now required)

Improved linear scaling (LS) DFT MD with curvy steps

Support for Hybrid density functionals in TDDFT

3.0 (December 22, 2015)



Improvement of the Path integral code and use of PIGLET thermostat

Workaround for ifort ‘feature’ leading to incorrectly ignored 1-4 interactions in classical MD

simulations.

Gradients for MP2 in the unrestricted case

Current output for EMD

constant E/D simulations

RMA based DBCSR

Improved portability (xlf90)

G0W0 and eigenvalue self-consistent GW

Improved testing: the make target ‘test’ will now regtest the code

Basic k-point functionality for GGA DFT

Faster TRS4 for semi-empirical runs.

Interface to the

PEXSI library

PLUMED

2.0 interface

Interface to ELPA2015

ELPA

Filtered Basis method

More optimized CUDA kernels

Coupling with the quantum transport code

OMEN

Implicit Poisson solver, with dielectric, and different boundary conditions

Rho mixing for LS SCF enabled

Speedup for LRIGPW method

Support for the

ASE

Python toolkit.

Updated

toolchain

Saveguard against known issue with CUDA cufft 7.0

Polarized atomic orbitals

REPEAT variant of the RESP atomic charge fitting method

Streamlined error handling

Support for Intel’s

libxsmm

Various bug fixes

2.6 (December 22, 2014)



Allowing GPU acceleration for full matrix multiplies by using the DBCSR multiply routines

RTP and EMD with Hartree-Fock exchange and ADMM NONE

Improved FULL_SINGLE_INVERSE preconditioner and linear scaling PRECOND_SOLVER INVERSE_UPDATE for

large systems

Self-consistent continuum solvation (SCCS) model

K-points (partial implementation for some methods)

Improved linear scaling routines.

Improved RPA frequency integration methods.

QUIP Manybody potential

Optimization of LRI basis sets

Full Fortran 2003 compliance

Various bug-fixes, refactoring, and speed-ups

Collection of production grade parameters (basis-sets, pseudo-potentials, etc.)

File discovery mechanism (controllable via compile flag

-D__DATA_DIR

or environment variable

$CP2K_DATA_DIR

)

New build-system, replaced makedepf90 with novel makedep.py

Started splitting code into sub-directories (packages) with well defined dependencies among each

other

Auto-tunning framework for DBCSR cuda-kernels and many readily optimized kernel-parameters

QM/MM for DFTB

LRIGPW

Hirshfeld population analysis

DM and Charge Constraint Projection based ADMM

2.5 (February 26, 2014)



MP2 gradients and stress

emacs plugin for input syntax highlighting (→

CP2K Tools

)

vim plugin for input syntax highlighting (→

CP2K Tools

)

Post-SCF linear response, including Raman

Energy use framework for Cray

RI-MP2 auxiliary basis optimization

Global optimization of geometries

SCP tight binding

Relativistic corrections for atomic blocks

CUDA enabled DBCSR

Improved OMP parallelism

Tree Monte Carlo: additional parallelism in MC

ALMO: linear scaling for molecular systems

Removed internal ELPA, using it as an external library instead

Integrated molecular basis set optimization

Langevin dynamics regions

DCD dump option for an aligned cell (allows a reconstruction of scaled coordinates)

and many bug fixes …

2.4 (June 13, 2013)



GPW-MP2 & RPA

Adaptive QM/MM

Non-local vDW functionals, PBEsol

Integrated basis set optimisation

Support for non-linear core corrected pseudos

Additional linear scaling algorithms and properties

Possibility of using image charges

Periodic RESP charges

PLUMED support

ELPA eigensolver support

libxc support

Improved ifort/MKL support

Process topology mapping for Cray Gemini

2.3 (Sept 03, 2012)



2.2 (Oct 23, 2011)



2.1 (Oct 6, 2010)



2.0 (Sep 8, 2009)


