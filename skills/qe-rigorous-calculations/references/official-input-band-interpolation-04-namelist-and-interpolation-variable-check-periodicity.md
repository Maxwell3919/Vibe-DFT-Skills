# INPUT_BAND_INTERPOLATION — NAMELIST: &INTERPOLATION — Variable: check_periodicity

- Official source: https://www.quantum-espresso.org/Doc/INPUT_BAND_INTERPOLATION.txt
- Retrieved: 2026-07-17T11:48:56+00:00
- Official source SHA-256: `b60e3891af78fc24ae40985e172e19ff674772d57eebe438f62dfd9a1e7a331f`
- Extracted text SHA-256: `0f4d0e4e27c51d0a73f013537426b6f767b21dde9ae83d174f312eb8835b2a36`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       check_periodicity
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    If .TRUE. a (time consuming) step is performed, to check whether all the Star functions have
                                     the correct lattice periodicity (only for "method" == 'fourier-diff' or 'fourier') .
                   
                                     For automatically generated Star functions this should never occur by construction, and the program
                                     will stop and exit in case one Star function with wrong periodicity is found (useful for
                                     debugging and program sanity check).
                   
                                     If additional user-defined Star vectors are specified (see optional card "USER_STARS"),
                                     the program will print a WARNING in case one Star function with wrong periodicity is found.
   +--------------------------------------------------------------------
   
```
