# INPUT_PW — NAMELIST: &CELL — Variable: cell_dynamics

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `4c9d69e698cc6488073d95b6a256c241d07e64fd2b1ec80cb5ff7d359bd98c27`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       cell_dynamics
   
   Type:           CHARACTER
   Description:   
                   Specify the type of dynamics for the cell.
                   For different type of calculation different possibilities
                   are allowed and different default values apply:
                   
                   CASE ( "calculation" == 'vc-relax' )
    
                   'none' :
                        no dynamics
    
                   'sd' :
                        steepest descent ( not implemented )
    
                   'damp-pr' :
                        damped (Beeman) dynamics of the Parrinello-Rahman extended lagrangian
    
                   'damp-w' :
                        damped (Beeman) dynamics of the new Wentzcovitch extended lagrangian
    
                   'bfgs' :
                        BFGS quasi-newton algorithm (default)
                        "ion_dynamics" must be 'bfgs' too
    
                   CASE ( "calculation" == 'vc-md' )
    
                   'none' :
                        no dynamics
    
                   'pr' :
                        (Beeman) molecular dynamics of the Parrinello-Rahman extended lagrangian
    
                   'w' :
                        (Beeman) molecular dynamics of the new Wentzcovitch extended lagrangian
   +--------------------------------------------------------------------
   
```
