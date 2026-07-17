# INPUT_PW — NAMELIST: &FCP — Variable: fcp_dynamics

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `46d54f8831d2854b3fa1de577c5d14e97f6e8e3fc1ea4d962ee5c79778c12812`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       fcp_dynamics
   
   Type:           CHARACTER
   Description:   
                   Specify the type of dynamics for the Fictitious Charge Particle (FCP).
                   
                   For different type of calculation different possibilities
                   are allowed and different default values apply:
                   
                   CASE ( "calculation" == 'relax' )
    
                   'bfgs' :
                        (default) BFGS quasi-newton algorithm, coupling with ions relaxation
                        "ion_dynamics" must be 'bfgs' too
    
                   'newton' :
                        Newton-Raphson algorithm with DIIS
                        "ion_dynamics" must be 'damp' too
    
                   'damp' :
                        damped (quick-min Verlet) dynamics for FCP relaxation
                        "ion_dynamics" must be 'damp' too
    
                   'lm' :
                        Line-Minimization algorithm for FCP relaxation
                        "ion_dynamics" must be 'damp' too
    
                   CASE ( "calculation" == 'md' )
    
                   'velocity-verlet' :
                        (default) Velocity-Verlet algorithm to integrate Newton's equation.
                        "ion_dynamics" must be 'verlet' too
    
                   'verlet' :
                        Verlet algorithm to integrate Newton's equation.
                        "ion_dynamics" must be 'verlet' too
   +--------------------------------------------------------------------
   
```
