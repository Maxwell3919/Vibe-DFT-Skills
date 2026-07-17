# INPUT_CP — NAMELIST: &ELECTRONS — Variable: electron_dynamics

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `902c85d53d027ea52919a2045182ca05fd6d48d7a8a009c4c4e034db3a57be89`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       electron_dynamics
   
   Type:           CHARACTER
   Default:        'none'
   Description:    set how electrons should be moved
                   'none'    : electronic degrees of freedom (d.o.f.) are kept fixed
                   'sd'      : steepest descent algorithm is used to minimize
                             electronic d.o.f.
                   'damp'    : damped dynamics is used to propagate electronic d.o.f.
                   'verlet'  : standard Verlet algorithm is used to propagate
                             electronic d.o.f.
                   'cg'      : conjugate gradient is used to converge the
                             wavefunction at each ionic step. 'cg' can be used
                             interchangeably with 'verlet' for a couple of ionic
                             steps in order to "cool down" the electrons and
                             return them back to the Born-Oppenheimer surface.
                             Then 'verlet' can be restarted again. This procedure
                             is useful when electronic adiabaticity in CP is lost
                             yet the ionic velocities need to be preserved.
   +--------------------------------------------------------------------
   
```
