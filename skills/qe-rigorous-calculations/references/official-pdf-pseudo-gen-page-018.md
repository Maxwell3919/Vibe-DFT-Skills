# pseudo-gen.pdf — page 18

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `f76e7fb8ea367af2b847f511369a8b6e7743ba7d62f036497d36e93bc88af7f9`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
      3 2     3D     1( 1.00)        -0.68514             -0.74236            0.05722
      1 0     4S     1( 2.00)        -0.45729             -0.45802            0.00073
      2 1     4P     1( 1.00)        -0.18855             -0.18471           -0.00383
      dEtot_ae =         0.343391 Ry
      dEtot_ps =         0.371650 Ry,    Delta E=             -0.028259 Ry

      3 2     3D     1( 1.00)        -1.16621             -1.21438            0.04817
      1 0     4S     1( 2.00)        -0.87720             -0.87620           -0.00100
      2 1     4P     1( 0.00)        -0.56807             -0.56137           -0.00670
      dEtot_ae =         0.716203 Ry
      dEtot_ps =         0.739110 Ry,    Delta E=             -0.022907 Ry

      3 2     3D     1( 1.00)        -1.82248             -1.87471            0.05223
      1 0     4S     1( 1.00)        -1.39447             -1.39936            0.00489
      2 1     4P     1( 0.00)        -1.03942             -1.03465           -0.00476
      dEtot_ae =         1.848995 Ry
      dEtot_ps =         1.873240 Ry,    Delta E=             -0.024245 Ry

      3 2     3D     1( 1.00)        -2.54976             -2.61959           0.06983
      1 0     4S     1( 0.00)        -1.94361             -1.96745           0.02383
      2 1     4P     1( 0.00)        -1.53584             -1.54419           0.00835
      dEtot_ae =         3.518170 Ry
      dEtot_ps =         3.554733 Ry,    Delta E=             -0.036564 Ry

      3 2     3D     1( 0.00)        -3.84145             -3.95251           0.11106
      1 0     4S     1( 0.00)        -2.73793             -2.81405           0.07612
      2 1     4P     1( 0.00)        -2.25938             -2.28768           0.02831
      dEtot_ae =         6.699594 Ry
      dEtot_ps =         6.831938 Ry,    Delta E=             -0.132344 Ry

It is evident that configurations with 3d2 occupancy are well reproduced, with errors
on total energy differences < 3 mRy and on eigenvalues< 5 mRy. Configurations with
different 3d occupancy, however, have errors one order of magnitude higher. For the
extreme case of Ti4+ , the error is ∼ 0.1 Ry.
    In order to better understand what is going on, let us have a look at the AE vs PS
orbitals and logarithmic derivatives for configuration 9 (i.e. for the bare PP). Let us
add a line like this:

   rlderiv=2.90, eminld=-4.0, emaxld=0.0, deld=0.01, nld=3,

and plot files ld19ps.wfc, ld19.dlog, ld19ps.dlog using gnuplot as above :
```
