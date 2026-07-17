# INPUT_MATDYN — NAMELIST: &INPUT — Variable: read_lr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_MATDYN.txt
- Retrieved: 2026-07-17T11:49:20+00:00
- Official source SHA-256: `e162a380590814b4ce7bce383261cbcae2567f7e9c21de8655af446082691b91`
- Extracted text SHA-256: `fb61737c8a4009ebf14699555779ec978780e1a0e5a2f5e8be4f26251463ae4d`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:08 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       read_lr
   
   Type:           LOGICAL
   Default:        .false.
   Description:    if .true. read also long-range force constants when they exist in
                   force constant file. This is required when enforcing "asr" = 'all'
                   for infrared-active solids.
   +--------------------------------------------------------------------
   
```
