# INPUT_CP — CARD: OCCUPATIONS

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `98baa48ec4def92a872cd1e1eabb8db146e631c5f13f72af4d26ebe021bcfc7b`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: OCCUPATIONS 

   OPTIONAL CARD, USED ONLY IF OCCUPATIONS = 'FROM_INPUT', IGNORED OTHERWISE !
   
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
      Description:    Occupations of individual states (MAX 10 PER LINE).
                      For spin-polarized calculations, these are majority spin states.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       f_inp2
      
      Type:           REAL
      Description:    Occupations of minority spin states (MAX 10 PER LINE)
                      To be specified only for spin-polarized calculations.
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
