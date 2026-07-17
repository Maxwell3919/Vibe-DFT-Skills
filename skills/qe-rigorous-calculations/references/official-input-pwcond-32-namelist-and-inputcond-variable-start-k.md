# INPUT_PWCOND — NAMELIST: &INPUTCOND — Variable: start_k

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PWCOND.txt
- Retrieved: 2026-07-17T11:49:48+00:00
- Official source SHA-256: `14fcee8af77391f494605bbcf53477d7c00e6d9e78555b3afd167462c8e53798`
- Extracted text SHA-256: `addf6e875b71a593df3c16c6050396bbdead3c5e875a68cb5441172e2e89e174`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       start_k
   
   Type:           INTEGER
   Default:        1
   See:            last_k
   Description:    if start_k > 1, the scattering problem is solved only for those
                   k-points with index between start_k and last_k in the k-point list.
                   In order to recover the full transmission (i.e. integrated over the
                   full Brillouin Zone) at the end, perform the partial runs specifying
                   a value for tran_prefix (the restart directory), then put all the
                   partial transmission files 'transmission_k#_e#' inside a unique
                   restart directory and run pwcond.x with recover=.TRUE. (without
                   specifying any value for start_k and last_k).
                   
                   NOTE: start_k <= last_k must be satisfied and start_k must also
                      not be greater than the actual number of k-point in the list
                      (if you compute the grid automatically by specifying the grid
                      size and shifts, you can use kpoints.x to check that number).
   +--------------------------------------------------------------------
   
```
