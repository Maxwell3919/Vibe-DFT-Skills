# INPUT_PW — NAMELIST: &SYSTEM — Variable: eamp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `15b1b46d4d08e1ece6b4b6f6856f270d239a00028abde21b0dfebdb16cb06e8a`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       eamp
   
   Type:           REAL
   Default:        0.001 a.u.
   Description:    Amplitude of the electric field, in ***Hartree*** a.u.;
                   1 a.u. = 51.4220632*10^10 V/m. Used only if "tefield"==.TRUE.
                   The saw-like potential increases with slope "eamp" in the
                   region from ("emaxpos"+"eopreg"-1) to ("emaxpos"), then decreases
                   to 0 until ("emaxpos"+"eopreg"), in units of the crystal
                   vector "edir". Important: the change of slope of this
                   potential must be located in the empty region, or else
                   unphysical forces will result.
   +--------------------------------------------------------------------
   
```
