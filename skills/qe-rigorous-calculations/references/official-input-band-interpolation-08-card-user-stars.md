# INPUT_BAND_INTERPOLATION — CARD: USER_STARS

- Official source: https://www.quantum-espresso.org/Doc/INPUT_BAND_INTERPOLATION.txt
- Retrieved: 2026-07-17T11:48:56+00:00
- Official source SHA-256: `b60e3891af78fc24ae40985e172e19ff674772d57eebe438f62dfd9a1e7a331f`
- Extracted text SHA-256: `412853b56a375277715083961fee1b580457dc5bfefa91753f4b613fe56704ce`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: USER_STARS 

   OPTIONAL CARD, USED ONLY IF "METHOD" == 'FOURIER-DIFF', OR 'FOURIER', IGNORED OTHERWISE !
   
   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
      USER_STARS 
         NUser
         vec_x(1)      vec_y(1)      vec_z(1)      
         vec_x(2)      vec_y(2)      vec_z(2)      
         . . . 
         vec_x(NUser)  vec_y(NUser)  vec_z(NUser)  
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Variable:       NUser
      
      Type:           INTEGER
      Default:        0
      Description:    Number of supplied additional Star vectors.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      vec_x, vec_y, vec_z
      
      Type:           REAL
      Description:    Additional user-defined Star vectors that are added to the
                      automatically generated ones to augment the Star functions
                      basis set.
                      You might also want to check "check_periodicity" when providing
                      user-defined Star vectors.
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
