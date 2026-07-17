# INPUT_PW — NAMELIST: &ELECTRONS — Variable: startingpot

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `c7613afba6b5d4b7e22cce39da4b89d39f7138750054362e808d2b7bd7dffc50`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       startingpot
   
   Type:           CHARACTER
   Description:   
                   Available options are:
    
                   'atomic' :
                        starting potential from atomic charge superposition
                        (default for scf, *relax, *md)
    
                   'file' :
                        start from existing "charge-density.xml" file in the
                        directory specified by variables "prefix" and "outdir"
                        For nscf and bands calculation this is the default
                        and the only sensible possibility.
   +--------------------------------------------------------------------
   
```
