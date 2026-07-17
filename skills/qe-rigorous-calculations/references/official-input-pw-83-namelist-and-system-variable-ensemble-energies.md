# INPUT_PW — NAMELIST: &SYSTEM — Variable: ensemble_energies

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `5b48cc3e4262f0c8efc6e9e15469a69053059a79f6d3ffaef320f2bf746471c5`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ensemble_energies
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If "ensemble_energies" = .true., an ensemble of xc energies
                   is calculated non-selfconsistently for perturbed
                   exchange-enhancement factors and LDA vs. PBE correlation
                   ratios after each converged electronic ground state
                   calculation.
                   
                   Ensemble energies can be analyzed with the 'bee' utility
                   included with libbeef.
                   
                   Requires linking against libbeef.
                   "input_dft" must be set to a BEEF-type functional
                   (e.g. input_dft = 'BEEF-vdW')
   +--------------------------------------------------------------------
   
```
