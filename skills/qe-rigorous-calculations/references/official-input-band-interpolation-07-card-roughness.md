# INPUT_BAND_INTERPOLATION — CARD: ROUGHNESS

- Official source: https://www.quantum-espresso.org/Doc/INPUT_BAND_INTERPOLATION.txt
- Retrieved: 2026-07-17T11:48:56+00:00
- Official source SHA-256: `b60e3891af78fc24ae40985e172e19ff674772d57eebe438f62dfd9a1e7a331f`
- Extracted text SHA-256: `126b0ac7a09472195a7c2c110754bae03a4ed23d17bcc4238cb94e1fe09c4998`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: ROUGHNESS 

   OPTIONAL CARD, USED ONLY IF "METHOD" == 'FOURIER-DIFF', OR 'FOURIER', IGNORED OTHERWISE!
   
   This card can be used to change the roughness functional that is minimized
                    in the "method" == 'fourier-diff' and 'fourier'.
                    In case "method" == 'fourier-diff', or 'fourier' and card ROUGHNESS is not specified the default
                    roughness will be used with "RoughN" == 1 and "RoughC"(1) == 1.0d0.
   
   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
      ROUGHNESS 
         RoughN
         RoughC(1)  RoughC(2)  . . .  RoughC(RoughN)  
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Variable:       RoughN
      
      Type:           INTEGER
      Default:        1
      Description:    Number of terms included in the roughness functional
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      RoughC
      
      Type:           REAL
      Default:        1.0d0
      Description:    Coefficients for the terms included in the roughness functional.
                                                      They can be explicitely given or 'automatic' can be specified instead of numbers
                                                      to use default coefficients.
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
