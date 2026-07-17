# INPUT_PW — NAMELIST: &SYSTEM — Variable: assume_isolated

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `107171b695097c320cbd37ffe71ca1acb6e2db2ac40db95345ea9b22988f5476`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       assume_isolated
   
   Type:           CHARACTER
   Default:        'none'
   Description:   
                   Used to perform calculation assuming the system to be
                   isolated (a molecule or a cluster in a 3D supercell).
                   
                   Currently available choices:
    
                   'none' :
                        (default): regular periodic calculation w/o any correction.
    
                   'makov-payne', 'm-p', 'mp' :
                        the Makov-Payne correction to the
                        total energy is computed. An estimate of the vacuum
                        level is also calculated so that eigenvalues can be
                        properly aligned. ONLY FOR CUBIC SYSTEMS ("ibrav"=1,2,3).
                        Theory: G.Makov, and M.C.Payne,
                             "Periodic boundary conditions in ab initio
                             calculations" , PRB 51, 4014 (1995).
    
                   'martyna-tuckerman', 'm-t', 'mt' :
                        Martyna-Tuckerman correction
                        to both total energy and scf potential. Adapted from:
                        G.J. Martyna, and M.E. Tuckerman,
                        "A reciprocal space based method for treating long
                        range interactions in ab-initio and force-field-based
                        calculation in clusters", J. Chem. Phys. 110, 2810 (1999),
                        doi:10.1063/1.477923.
    
                   'esm' :
                        Effective Screening Medium Method.
                        For polarized or charged slab calculation, embeds
                        the simulation cell within an effective semi-
                        infinite medium in the perpendicular direction
                        (along z). Embedding regions can be vacuum or
                        semi-infinite metal electrodes (use "esm_bc" to
                        choose boundary conditions). If between two
                        electrodes, an optional electric field
                        ("esm_efield") may be applied. Method described in
                        M. Otani and O. Sugino, "First-principles calculations
                        of charged surfaces and interfaces: A plane-wave
                        nonrepeated slab approach", PRB 73, 115407 (2006).
                        
                        NB:
                           - Two dimensional (xy plane) average charge density
                             and electrostatic potentials are printed out to
                             'prefix.esm1'.
                        
                           - Requires cell with a_3 lattice vector along z,
                             normal to the xy plane, with the slab centered
                             around z=0.
                        
                           - For bc2 with an electric field and bc3 boundary
                             conditions, the inversion symmetry along z-direction
                             is automatically eliminated.
                        
                           - In case of calculation='vc-relax', use
                             "cell_dofree"='2Dxy' or other parameters so that
                             c-vector along z-axis should not be moved.
                        
                        See "esm_bc", "esm_efield", "esm_w", "esm_nfit".
    
                   '2D' :
                        Truncation of the Coulomb interaction in the z direction
                        for structures periodic in the x-y plane. Total energy,
                        forces and stresses are computed in a two-dimensional framework.
                        Linear-response calculations () done on top of a self-consistent
                        calculation with this flag will automatically be performed in
                        the 2D framework as well. Please refer to:
                        Sohier, T., Calandra, M., & Mauri, F. (2017), "Density functional
                        perturbation theory for gated two-dimensional heterostructures:
                        Theoretical developments and application to flexural phonons in graphene",
                        PRB, 96, 075448 (2017).
                        
                        NB:
                           - The length of the unit-cell along the z direction should
                             be larger than twice the thickness of the 2D material
                             (including electrons). A reasonable estimate for a
                             layer's thickness could be the interlayer distance in the
                             corresponding layered bulk material. Otherwise,
                             the atomic thickness + 10 bohr should be a safe estimate.
                             There is also a lower limit of 20 bohr imposed by the cutoff
                             radius used to read pseudopotentials (see read_pseudo.f90 in Modules).
                        
                           - As for ESM above, only in-plane stresses make sense and one
                             should use "cell_dofree"= '2Dxy' in a vc-relax calculation.
   +--------------------------------------------------------------------
   
```
