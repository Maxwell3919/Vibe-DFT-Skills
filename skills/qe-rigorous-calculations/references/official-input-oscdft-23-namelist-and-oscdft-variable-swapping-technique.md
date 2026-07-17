# INPUT_OSCDFT — NAMELIST: &OSCDFT — Variable: swapping_technique

- Official source: https://www.quantum-espresso.org/Doc/INPUT_OSCDFT.txt
- Retrieved: 2026-07-17T11:49:28+00:00
- Official source SHA-256: `e91edda1595da7b1c15244530b31ab9368e0fc0bad5146f74c1dcfeb21a95888`
- Extracted text SHA-256: `3e6318459655d7d96395e48e5275ca17fc197a6c1c8cfa5f4236aaa273d74c7e`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       swapping_technique
   
   Type:           CHARACTER
   Default:        'none'
   Description:   
                   See ""://doi.org/10.1021/acs.jctc.9b00281
    
                   'none' :
                        No swapping technique.
                        Always chooses the occupation number in ascending order.
    
                   'permute' :
                        Chooses the occupation number associated with the
                        occupation eigenvector that is most similar compared
                        to previous iteration (using dot product)
   +--------------------------------------------------------------------
   
```
