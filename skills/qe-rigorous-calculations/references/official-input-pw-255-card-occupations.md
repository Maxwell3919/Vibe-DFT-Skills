# INPUT_PW — CARD: OCCUPATIONS

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `7fcced3f9a65b4a394c0dfde9e24b5d1b13e8ba54dad03c5c4cf97427d612648`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: OCCUPATIONS 

   OPTIONAL CARD, USED ONLY IF "OCCUPATIONS" == 'FROM_INPUT', IGNORED OTHERWISE !
   
   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
      OCCUPATIONS 
           f_inp1(1)  f_inp1(2)  . . .  f_inp1(nbnd)  
         [ f_inp2(1)  f_inp2(2)  . . .  f_inp2(nbnd)  ] 
         
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Variable:       f_inp1
      
      Type:           REAL
      Description:    Occupations of individual states (MAX 10 PER ROW).
                      For spin-polarized calculations, these are majority spin states.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       f_inp2
      
      Type:           REAL
      Description:    Occupations of minority spin states (MAX 10 PER ROW)
                      To be specified only for spin-polarized calculations.
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
