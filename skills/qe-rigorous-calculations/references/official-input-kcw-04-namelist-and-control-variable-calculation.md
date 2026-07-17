# INPUT_kcw — NAMELIST: &CONTROL — Variable: calculation

- Official source: https://www.quantum-espresso.org/Doc/INPUT_kcw.txt
- Retrieved: 2026-07-17T11:49:55+00:00
- Official source SHA-256: `0e051e12dbf1f904e8044c5f2fc1f44a8e2f8f72f29e687d4fd675364d26e3d0`
- Extracted text SHA-256: `28a9e55452a0b553140cbbdcc561a9589d1cbab7a502e201f787e8f39f98d8a2`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       calculation
   
   Type:           CHARACTER
   Default:        ' '
   Description:   
                   Specify the KCW calculation to be done
                   Possible choices:
    
                   'wann2kcw' :
                        Pre-processing to prepare KCW calculation.
                        Read previous PWSCF and possibly W90 outputs and prepare the KCW
                        calculation
    
                   'screen' :
                        Perform the calculation of KCW screening coefficient using a
                        LR approach as described here https://doi.org/10.1021/acs.jctc.7b01116
                        and arXiv:2202.08155
    
                   'ham' :
                        Perform the calculation interpolation and diagonalization of the KI hamiltonian
    
                   'cc' :
                        Computes the (estimated) q+G=0 contribution to the bare and screened KC corrections.
                        A report on this quantities is printed on output and can be used to correct a
                        posteriori a "screen" calculation performed without any corrective scheme ("l_vcut"=.false.)
                        avoiding the need of re-doing a "screen" calculation.
   +--------------------------------------------------------------------
   
```
