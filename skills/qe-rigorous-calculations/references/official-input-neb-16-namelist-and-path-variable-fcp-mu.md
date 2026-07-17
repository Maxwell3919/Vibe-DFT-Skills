# INPUT_NEB — NAMELIST: &PATH — Variable: fcp_mu

- Official source: https://www.quantum-espresso.org/Doc/INPUT_NEB.txt
- Retrieved: 2026-07-17T11:49:26+00:00
- Official source SHA-256: `7c9f7e082b4846135e360fb86c0ce8a43f8e63825fa7d7fafcda3836a6088706`
- Extracted text SHA-256: `945b95a3a58706bc24fec111b132d7da2e95c705dfd31bd45fb5e4529f60b0d9`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
         +--------------------------------------------------------------------
         Variable:       fcp_mu
         
         Type:           REAL
         See:            lfcp
         Default:        0.d0
         Description:    If "lfcp" == .TRUE., gives the target Fermi energy [eV].
                         One can specify the total charge of the system for the first
                         and last image by giving "TOTAL_CHARGE" cards
                         so that the Fermi energy of these systems will be the target value,
                         otherwise "first_last_opt" should be .TRUE.
                         For the initial charge of intermediate images, the "TOTAL_CHARGE"
                         is linearly interpolated between the initial and the final ones
                         unless the "TOTAL_CHARGE" is given in the input file.
         +--------------------------------------------------------------------
         
```
