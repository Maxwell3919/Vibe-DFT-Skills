# INPUT_pw2bgw — NAMELIST: &INPUT_PW2BGW — Variable: vxc_zero_rho_core

- Official source: https://www.quantum-espresso.org/Doc/INPUT_pw2bgw.txt
- Retrieved: 2026-07-17T11:49:58+00:00
- Official source SHA-256: `5f52150cf5d567429fbca7663ea1ecd3841683947b6ecfd410873e0a6d134e55`
- Extracted text SHA-256: `23509ad9a29836e9cb620091b8b12c190c406a0c4ff08430aec978dcd5dfac87`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       vxc_zero_rho_core
   
   Type:           LOGICAL
   Default:        .TRUE.
   Description:    set to .TRUE. to zero out NLCC or to .FALSE. to keep NLCC when computing
                   exchange-correlation potential. This flag has no effect for pseudopotentials
                   without NLCC.
                   BEWARE: setting "vxc_zero_rho_core" to .FALSE. will produce
                   incorrect results. This functionality is only included for testing purposes
                   and is not meant to be used in a production environment
   +--------------------------------------------------------------------
   
```
