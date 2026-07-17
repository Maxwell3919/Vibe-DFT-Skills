# INPUT_CP — NAMELIST: &IONS — Variable: ion_dynamics

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `6c28f1b5b74a3c1306c421843bf2eec1eeba7f46b8209e444df5d682b7418dd0`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ion_dynamics
   
   Type:           CHARACTER
   Description:    Specify the type of ionic dynamics.
                   
                    For constrained dynamics or constrained optimisations add the
                    CONSTRAINTS card (when the card is present the SHAKE algorithm is
                                      automatically used).
                   'none'    : ions are kept fixed
                   'sd'      : steepest descent algorithm is used to minimize ionic
                               configuration
                   'cg'      : conjugate gradient algorithm is used to minimize ionic
                               configuration
                   'damp'    : damped dynamics is used to propagate ions
                   'verlet'  : standard Verlet algorithm is used to propagate ions
   +--------------------------------------------------------------------
   
```
