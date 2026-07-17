# INPUT_CP — NAMELIST: &ELECTRONS — Variable: orthogonalization

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `062a892ee0e31f1529be712c3cb1bc8db6bca7a21fa1c68ab2318b87e752ee4a`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       orthogonalization
   
   Type:           CHARACTER
   Default:        'ortho'
   Description:    selects the orthonormalization method for electronic wave
                   functions
                   'ortho'        : use iterative algorithm - if it doesn't converge,
                                    reduce the timestep, or use options ortho_max
                                    and ortho_eps, or use Gram-Schmidt instead just
                                    to start the simulation
                   'Gram-Schmidt' : use Gram-Schmidt algorithm - to be used ONLY in
                                    the first few steps.
                                    YIELDS INCORRECT ENERGIES AND EIGENVALUES.
   +--------------------------------------------------------------------
   
```
