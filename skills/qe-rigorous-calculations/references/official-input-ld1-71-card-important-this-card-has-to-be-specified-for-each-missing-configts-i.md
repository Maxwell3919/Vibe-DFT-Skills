# INPUT_LD1 — CARD: IMPORTANT: THIS CARD HAS TO BE SPECIFIED FOR EACH MISSING CONFIGTS(I)

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `e6af939c76ef66125a96b7518835924e9f93daed196cef650d6d204920592591`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD:  

   IMPORTANT: THIS CARD HAS TO BE SPECIFIED FOR EACH MISSING CONFIGTS(I)
   
   ________________________________________________________________________
   * IF lsd=1 : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
            nwfts
            elts(1)      nnts(1)      llts(1)      octs(1)      enerts(1)      rcutts(1)      rcutusts(1)      iswts(1)      
            elts(2)      nnts(2)      llts(2)      octs(2)      enerts(2)      rcutts(2)      rcutusts(2)      iswts(2)      
            . . . 
            elts(nwfts)  nnts(nwfts)  llts(nwfts)  octs(nwfts)  enerts(nwfts)  rcutts(nwfts)  rcutusts(nwfts)  iswts(nwfts)  
      
      /////////////////////////////////////////
      
       
   * ELSE IF rel=2 : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
            nwfts
            elts(1)      nnts(1)      llts(1)      octs(1)      enerts(1)      rcutts(1)      rcutusts(1)      jjts(1)      
            elts(2)      nnts(2)      llts(2)      octs(2)      enerts(2)      rcutts(2)      rcutusts(2)      jjts(2)      
            . . . 
            elts(nwfts)  nnts(nwfts)  llts(nwfts)  octs(nwfts)  enerts(nwfts)  rcutts(nwfts)  rcutusts(nwfts)  jjts(nwfts)  
      
      /////////////////////////////////////////
      
       
   * ELSE : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
            nwfts
            elts(1)      nnts(1)      llts(1)      octs(1)      enerts(1)      rcutts(1)      rcutusts(1)      
            elts(2)      nnts(2)      llts(2)      octs(2)      enerts(2)      rcutts(2)      rcutusts(2)      
            . . . 
            elts(nwfts)  nnts(nwfts)  llts(nwfts)  octs(nwfts)  enerts(nwfts)  rcutts(nwfts)  rcutusts(nwfts)  
      
      /////////////////////////////////////////
      
       
   ENDIF
   ________________________________________________________________________
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Variable:       nwfts
      
      Type:           INTEGER
      Description:    number of wavefunctions
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       elts
      
      Type:           CHARACTER
      See:            nls
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       nnts
      
      Type:           INTEGER
      See:            nns
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       llts
      
      Type:           INTEGER
      See:            lls
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       octs
      
      Type:           REAL
      See:            ocs
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       enerts
      
      Type:           REAL
      Status:         not used
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       rcutts
      
      Type:           REAL
      Status:         not used
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       rcutusts
      
      Type:           REAL
      Status:         not used
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       iswts
      
      Type:           INTEGER
      Description:    spin index (1 or 2, used in lsda case)
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       jjts
      
      Type:           REAL
      Description:    total angular momentum of the state
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================



:::: Notes

   For PP generation you do not need to specify namelist &test, UNLESS:
   
   1. you want to use a different configuration for unscreening wrt the
   one used to generate the PP. This is useful for PP with semicore
   states: use semicore states ONLY to produce the PP, use semicore
   AND valence states (if occupied) to make the unscreening
   
   2. you want to specify some more states for PAW style reconstruction of
   all-electron orbitals from pseudo-orbitals
   
   
   ::: Output files written
   
      * file_tests            "prefix".test    results of transferability test
      
      for each testing configuration N:
      
      * file_wavefunctions    "prefix"N.wfc     all-electron KS orbitals
      * file_wavefunctionsps  "prefix"Nps.wfc   pseudo KS orbitals
      
      if lsd=1:
      
      * file_wavefunctions    "prefix"N.wfc.up  all-electron KS up orbitals
      * file_wavefunctions    "prefix"N.wfc.dw  all-electron KS down orbitals
      
      if rel=2 and lsmall=.true.:
      
      * file_wavefunctions    "prefix".wfc.small  all-electron KS small component
      
      if parameters for logarithmic derivatives are specified:
      
      * file_logder           "prefix"Nps.dlog  all-electron logarithmic derivatives
      * file_logderps         "prefix"Nps.dlog  pseudo logarithmic derivatives
      
      "N" is not present if there is just one testing configuration.
      

   
   ::: Recipes to reproduce old all-electron atomic results with the ld1 program
   
      * The Hartree results in Phys. Rev. 59, 299 (1940) or in
        Phys. Rev. 59, 306 (1940) can be reproduced with:
      
          rel=0,
          isic=1,
          dft='NOX-NOC'
      
      * The Herman-Skillman tables can be reproduced with:
      
          rel=0,
          isic=0,
          latt=1,
          dft='SL1-NOC'
      
      * Data on the paper Liberman, Waber, Cromer Phys. Rev. 137, A27 (1965) can be
      reproduced with:
      
          rel=2,
          isic=0,
          latt=1,
          dft='SL1-NOC'
      
      * Data on the paper S. Cohen Phys. Rev. 118, 489 (1960) can be reproduced with:
      
          rel=2,
          isic=1,
          latt=0,
          dft='NOX-NOC'
      
      * The revised PBE described in PRL 80, 890 (1998) can be obtained with:
      
          isic=0
          latt=0
          dft='SLA-PW-RPB-PBC' or 'dft='revPBE'
      
      * The relativistic energies of closed shell atoms reported in PRB 64 235126 (2001)
      can be reproduced with:
      
          isic=0
          latt=0
          cau_fact=137.0359895
          dft='sla-vwn' for the LDA case
          dft='PBE'     for the PBE case
      
      * The NIST results in PRA 55, 191 (1997):
      
          LDA:
              rel=0
              dft='sla-vwn'
      
          LSD:
              rel=0
              lsd=1
              dft='sla-vwn'
      
          RLDA
              rel=2
              rel_dist='average'
              dft='rxc-vwn'
      
          ScRLDA:
              rel=1
              dft='rxc-vwn'
      


This file has been created by helpdoc utility on Wed Oct 16 19:29:41 CEST 2024
```
