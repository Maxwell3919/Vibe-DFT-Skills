# INPUT_PW — NAMELIST: &CONTROL — Variable: gate

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `c3e473b87c4dcfd682b9f29e8cb7c361997986fa622ec157e356a421c4d085e1`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       gate
   
   Type:           LOGICAL
   Default:        .FALSE.
   See:            zgate, relaxz, block, block_1, block_2, block_height
   Description:    In the case of charged cells ("tot_charge" .ne. 0) setting gate = .TRUE.
                   represents the counter charge (i.e. -tot_charge) not by a homogeneous
                   background charge but with a charged plate, which is placed at "zgate"
                   (see below). Details of the gate potential can be found in
                   T. Brumme, M. Calandra, F. Mauri; PRB 89, 245406 (2014).
                   Note, that in systems which are not symmetric with respect to the plate,
                   one needs to enable the dipole correction! ("dipfield"=.true.).
                   Currently, symmetry can be used with gate=.true. but carefully check
                   that no symmetry is included which maps z to -z even if in principle one
                   could still use them for symmetric systems (i.e. no dipole correction).
                   For "nosym"=.false. verbosity is set to 'high'.
                   Note: this option was called "monopole" in v6.0 and 6.1 of pw.x
   +--------------------------------------------------------------------
   
```
