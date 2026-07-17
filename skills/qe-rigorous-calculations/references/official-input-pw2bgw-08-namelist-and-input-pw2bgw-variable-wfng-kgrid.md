# INPUT_pw2bgw — NAMELIST: &INPUT_PW2BGW — Variable: wfng_kgrid

- Official source: https://www.quantum-espresso.org/Doc/INPUT_pw2bgw.txt
- Retrieved: 2026-07-17T11:49:58+00:00
- Official source SHA-256: `5f52150cf5d567429fbca7663ea1ecd3841683947b6ecfd410873e0a6d134e55`
- Extracted text SHA-256: `de1f7428e4997d7e3204cb1948d82c768a56644a9b60e9f8156620240ad1d457`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       wfng_kgrid
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    overwrite k-grid parameters in BerkeleyGW WFN file.
                   If pw.x input file contains an explicit list of k-points,
                   the k-grid parameters in the output of pw.x will be set to zero.
                   Since sigma and absorption in BerkeleyGW both need to know the
                   k-grid dimensions, we patch these parameters into BerkeleyGW WFN file
   +--------------------------------------------------------------------
   
```
