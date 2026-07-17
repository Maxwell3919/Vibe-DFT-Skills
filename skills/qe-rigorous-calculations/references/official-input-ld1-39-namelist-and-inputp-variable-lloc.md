# INPUT_LD1 — NAMELIST: &INPUTP — Variable: lloc

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `c79090685c876751ef2fb21569f96289a4046791ce6a4381f11960563389ed7b`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       lloc
   
   Type:           INTEGER
   Default:        -1
   Description:    Angular momentum of the local channel.
                   
                   * lloc=-1 or lloc=-2 pseudizes the all-electron potential
                     if lloc=-2 the original recipe of Troullier-Martins
                     is used (zero first and second derivatives at r=0)
                   * lloc>-1 uses the corresponding channel as local PP
                   
                   NB: if lloc>-1, the corresponding channel must be the last in the
                   list of wavefunctions appearing after the namelist &inputp
                   In the relativistic case, if lloc > 0 both the j=lloc-1/2 and
                   the j=lloc+1/2 wavefunctions must be at the end of the list.
   +--------------------------------------------------------------------
   
```
