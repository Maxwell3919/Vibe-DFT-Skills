# INPUT_Davidson — NAMELIST: &LR_DAV — Variable: if_random_init

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Davidson.txt
- Retrieved: 2026-07-17T11:49:12+00:00
- Official source SHA-256: `3119323bee658797174ac83c6f304a99ae95949a07ca87563de949ec1243341c`
- Extracted text SHA-256: `cb0209bdfddaaf23279f782a752f418ee0cd0f3306329276f8312fb354ee443c`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       if_random_init
   
   Type:           LOGICAL
   Default:        .false.
   Description:    When set to .true. trial vectors are chosen randomly, otherwise
                   they are guessed from the ground-state calculation.
                   If "p_nbnd_occ" * "p_nbnd_virt" < "num_init", this term
                   is forced to be .true. The usage of random trial vectors should
                   cause only a slower convergence, and do not affect the final results.
   +--------------------------------------------------------------------
   
```
