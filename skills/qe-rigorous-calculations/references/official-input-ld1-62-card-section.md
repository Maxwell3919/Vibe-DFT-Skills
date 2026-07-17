# INPUT_LD1 — CARD: ________________________________________________________________________

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `1a60a7a7b33ec7b61fdba139168e3d58fbd75ccd216f4f46b3b4c20f698a04d1`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD:  

   ________________________________________________________________________
   * IF rel=0  OR  rel=2 : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
            nwfs
            nls(1)     nns(1)     lls(1)     ocs(1)     ener(1)     rcut(1)     rcutus(1)     jjs(1)     
            nls(2)     nns(2)     lls(2)     ocs(2)     ener(2)     rcut(2)     rcutus(2)     jjs(2)     
            . . . 
            nls(nwfs)  nns(nwfs)  lls(nwfs)  ocs(nwfs)  ener(nwfs)  rcut(nwfs)  rcutus(nwfs)  jjs(nwfs)  
      
      /////////////////////////////////////////
      
      * if "lloc">-1 the state with "lls"="lloc" must be the last
      
      * if "lloc">0 in the relativistic case, both states with "jjs"="lloc"-1/2
        and "jjs"="lloc"+1/2 must be the last two
      
       
   * ELSE : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
            nwfs
            nls(1)     nns(1)     lls(1)     ocs(1)     ener(1)     rcut(1)     rcutus(1)     
            nls(2)     nns(2)     lls(2)     ocs(2)     ener(2)     rcut(2)     rcutus(2)     
            . . . 
            nls(nwfs)  nns(nwfs)  lls(nwfs)  ocs(nwfs)  ener(nwfs)  rcut(nwfs)  rcutus(nwfs)  
      
      /////////////////////////////////////////
      
       
   ENDIF
   ________________________________________________________________________
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Variable:       nwfs
      
      Type:           INTEGER
      Description:    number of wavefunctions to be pseudized
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       nls
      
      Type:           CHARACTER
      Description:    Wavefunction label (same as in the all-electron configuration).
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       nns
      
      Type:           INTEGER
      Description:    Principal quantum number (referred to the PSEUDOPOTENTIAL case;
                      nns=1 for lowest s, nns=2 for lowest p, and so on).
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       lls
      
      Type:           INTEGER
      Description:    Angular momentum quantum number.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       ocs
      
      Type:           REAL
      Description:    Occupation number  (same as in the all-electron configuration).
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       ener
      
      Type:           REAL
      Description:    Energy (Ry) used to pseudize the corresponding state.
                      If 0.d0, use the one-electron energy of the all-electron state.
                      Do not use 0.d0 for unbound states!
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       rcut
      
      Type:           REAL
      Description:    Matching radius (a.u.) for norm conserving PP.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       rcutus
      
      Type:           REAL
      Description:    Matching radius (a.u.) for ultrasoft PP - only for pseudotype=3.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       jjs
      
      Type:           REAL
      Description:    The total angular momentum (0.0 is allowed for complete shells).
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
