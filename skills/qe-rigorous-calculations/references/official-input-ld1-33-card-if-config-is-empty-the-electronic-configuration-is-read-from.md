# INPUT_LD1 — CARD: IF CONFIG IS EMPTY THE ELECTRONIC CONFIGURATION IS READ FROM

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `0a6dfbf96592f8e92e3092ef49f5af151f1516898c9285e3751c0969b897351a`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD:  

   IF CONFIG IS EMPTY THE ELECTRONIC CONFIGURATION IS READ FROM
   THE FOLLOWING CARDS:
   
   ________________________________________________________________________
   * IF rel < 2 : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
            nwf
            nl(1)    n(1)    l(1)    oc(1)    isw(1)    
            nl(2)    n(2)    l(2)    oc(2)    isw(2)    
            . . . 
            nl(nwf)  n(nwf)  l(nwf)  oc(nwf)  isw(nwf)  
      
      /////////////////////////////////////////
      
       
   * ELSE IF rel = 2 : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
            nwf
            nl(1)    n(1)    l(1)    oc(1)    jj(1)    
            nl(2)    n(2)    l(2)    oc(2)    jj(2)    
            . . . 
            nl(nwf)  n(nwf)  l(nwf)  oc(nwf)  jj(nwf)  
      
      /////////////////////////////////////////
      
       
   ENDIF
   ________________________________________________________________________
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Variable:       nwf
      
      Type:           INTEGER
      Description:    number of wavefunctions
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       nl
      
      Type:           CHARACTER
      Description:    wavefunction label (e.g. 1s, 2s, etc.)
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       n
      
      Type:           INTEGER
      Description:    principal quantum number
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       l
      
      Type:           INTEGER
      Description:    angular quantum number
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       oc
      
      Type:           REAL
      Description:    occupation number
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       isw
      
      Type:           INTEGER
      Description:    the spin index (1-2) used only in the lsda case
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       jj
      
      Type:           REAL
      Description:    The total angular momentum (0.0 is allowed for complete
                      shells: the codes fills 2l states with jj=l-1/2,
                      2l+2 with jj=l+1/2).
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
