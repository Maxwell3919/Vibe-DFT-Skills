# INPUT_PW — NAMELIST: &IONS — Variable: ion_dynamics

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `3814fd119b0f264afdbf09dc4f49ac7aef5c94495e999757138e769b36f2245a`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ion_dynamics
   
   Type:           CHARACTER
   Description:   
                   Specify the type of ionic dynamics.
                   
                   For different type of calculation different possibilities are
                   allowed and different default values apply:
                   
                   CASE ( "calculation" == 'relax' )
    
                   'bfgs' :
                        (default)  use BFGS quasi-newton algorithm,
                        based on the trust radius procedure,
                        for structural relaxation
    
                   'damp' :
                        use damped (quick-min Verlet)
                        dynamics for structural relaxation
                        Can be used for constrained
                        optimisation: see "CONSTRAINTS" card
    
                   'fire' :
                        use the FIRE minimization algorithm employing the
                                semi-implicit Euler integration scheme
                                see:
                                Bitzek et al.,PRL, 97, 170201, (2006), doi: 10.1103/PhysRevLett.97.170201
                                Guenole et al.,CMS, 175, 109584, (2020), doi: 10.1016/j.commatsci.2020.109584
                        
                        Can be used for constrained optimisation: see "CONSTRAINTS" card
    
                   CASE ( "calculation" == 'md' )
    
                   'verlet' :
                        (default)  use Verlet algorithm to integrate
                        Newton's equation. For constrained
                        dynamics, see "CONSTRAINTS" card
    
                   'velocity-verlet' :
                        use velocity-Verlet algorithm to integrate Newton's equation.
                        For constrained dynamics, see "CONSTRAINTS" card.
    
                   'langevin' :
                        ion dynamics is over-damped Langevin
    
                   'langevin-smc' :
                        over-damped Langevin with Smart Monte Carlo:
                        see R.J. Rossky, JCP, 69, 4628 (1978), doi:10.1063/1.436415
    
                   CASE ( "calculation" == 'vc-relax' )
    
                   'bfgs' :
                        (default)  use BFGS quasi-newton algorithm;
                        "cell_dynamics" must be 'bfgs' too
    
                   'damp' :
                        use damped (Beeman) dynamics for
                        structural relaxation
    
                   CASE ( "calculation" == 'vc-md' )
    
                   'beeman' :
                        (default)  use Beeman algorithm to integrate
                        Newton's equation
   +--------------------------------------------------------------------
   
```
