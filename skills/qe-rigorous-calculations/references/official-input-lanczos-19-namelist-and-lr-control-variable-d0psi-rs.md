# INPUT_Lanczos — NAMELIST: &LR_CONTROL — Variable: d0psi_rs

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Lanczos.txt
- Retrieved: 2026-07-17T11:49:18+00:00
- Official source SHA-256: `58c02f4cb1fdefbef4203bbe55d16af2a768acd7cfb5462fc62bd1dfd07cb530`
- Extracted text SHA-256: `30aacc2b8a7648b1566c1e0bdf23fb2f48ec043d7c4a855036513f7d04bc5d17`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       d0psi_rs
   
   Type:           LOGICAL
   Default:        .false.
   Description:    When set to .true. the dipole is computed in the
                   real space. When set to .false. the dipole is
                   computed in the reciprocal space by computing [H,r].
                   Note, currently the commutator does not contain
                   a contribution for hybrids [V_EXX,r]. See also
                   the variable lshift_d0psi.
                   Important: Treatment of the dipole in the real space
                   is allowed only if the system is finite.
   +--------------------------------------------------------------------
   
```
