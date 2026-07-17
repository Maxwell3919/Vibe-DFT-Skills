# INPUT_PPACF — NAMELIST: &PPACF — Variable: lplot

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PPACF.txt
- Retrieved: 2026-07-17T11:49:41+00:00
- Official source SHA-256: `ec18cfa677f3d5684e7176a867c5d56868b44758bd2d43678d4ee813e1ecfc39`
- Extracted text SHA-256: `5bb9efcc5dcbfc7cb19bd134ddd9550f1c713d773fbe9cf1370ac079b9985ab1`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       lplot
   
   Type:           LOGICAL
   Description:    If .True. print out the spatial distribution of energy density.
                   prefix.tclda             the LDA component of kinetic-correlation energy density.
                   prefix.tcnl(prefix.tcgc) the non-local (gradient corrected) component of kinetic-correlation energy density.
                   prefix.exlda             the LDA component of exchange energy density.
                   prefix.eclda             the LDA component of correlation energy density.
                   prefix.exgc              the gradient-corrected component of exchange energy density.
                   prefix.ecnl(prefix.ecgc) the non-local(gradient-corrected) component of correlation energy density.
                   prefix.vcnl                  If vdW-DF: the non-local correlation-potential variation (at nspin=1).
                   prefix.vcnl1,2                 If spin-vdW-DF: spin-reolved non-local correlation-potential variations.
   Default:        .False.
   +--------------------------------------------------------------------
   
   ________________________________________________________________________
   * IF lplot=.True. : 
   
      OPTION FOR PLOT (LPLOT=.TRUE.):
      
```
