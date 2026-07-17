# INPUT_PW — NAMELIST: &ELECTRONS — Variable: diago_david_ndim

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `b41b7854e430ae607e4084cab74d9d958526272e4b0a61a11f4dffada17f44fc`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       diago_david_ndim
   
   Type:           INTEGER
   Default:        2
   Description:    For Davidson diagonalization: dimension of workspace
                   (number of wavefunction packets, at least 2 needed).
                   A larger value may yield a smaller number of iterations in
                   the algorithm but uses more memory and more CPU time in
                   subspace diagonalization (cdiaghg/rdiaghg). You may try
                   "diago_david_ndim"=4 if you are not tight on memory
                   and if the time spent in subspace diagonalization is small
                   compared to the time spent in h_psi
   +--------------------------------------------------------------------
   
```
