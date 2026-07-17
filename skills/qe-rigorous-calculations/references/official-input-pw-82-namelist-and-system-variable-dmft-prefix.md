# INPUT_PW — NAMELIST: &SYSTEM — Variable: dmft_prefix

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `389fa4c4c5510dfe6362a037334b56e2de2903e8b33faca996283d3bf3e38d92`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       dmft_prefix
   
   Type:           CHARACTER
   Default:        "prefix"
   Description:    prepended to hdf5 archive: dmft_prefix.h5
                   
                   DMFT update should be provided in group/dataset as:
                   - dft_misc_input/band_window with dimension [1, number of k-points, 2 (real + complex)]
                   - dft_update/delta_N with dimension [number of k-points, number of correlated orbitals,
                   number of correlated orbitals, 2 (real + complex)]
   +--------------------------------------------------------------------
   
```
