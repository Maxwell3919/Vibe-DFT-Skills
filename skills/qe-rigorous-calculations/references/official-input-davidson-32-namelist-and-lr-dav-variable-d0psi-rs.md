# INPUT_Davidson — NAMELIST: &LR_DAV — Variable: d0psi_rs

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Davidson.txt
- Retrieved: 2026-07-17T11:49:12+00:00
- Official source SHA-256: `3119323bee658797174ac83c6f304a99ae95949a07ca87563de949ec1243341c`
- Extracted text SHA-256: `4caa0d4c995a824aef107579d953cf83321c7c93dd49d63458e49e414195f2a1`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
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
                   the variable "lshift_d0psi".
                   Important: Treatment of the dipole in the real space
                   is allowed only if the system is finite.
   +--------------------------------------------------------------------
   
```
