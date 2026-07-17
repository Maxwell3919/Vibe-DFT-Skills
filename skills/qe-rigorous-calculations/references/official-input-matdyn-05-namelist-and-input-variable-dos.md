# INPUT_MATDYN — NAMELIST: &INPUT — Variable: dos

- Official source: https://www.quantum-espresso.org/Doc/INPUT_MATDYN.txt
- Retrieved: 2026-07-17T11:49:20+00:00
- Official source SHA-256: `e162a380590814b4ce7bce383261cbcae2567f7e9c21de8655af446082691b91`
- Extracted text SHA-256: `ac8c60077d3cf873eb590d554828aea61b02589f42b055aa962b02cd4dacf15b`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:08 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       dos
   
   Type:           LOGICAL
   Description:    if .true. calculate phonon Density of States (DOS)
                   using tetrahedra and a uniform q-point grid (see below)
                   NB: may not work properly in noncubic materials
                   
                   if .false. calculate phonon bands from the list of q-points
                   supplied in input (default)
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      nk1, nk2, nk3
   
   Type:           INTEGER
   Description:    uniform q-point grid for DOS calculation (includes q=0)
                   (must be specified if "dos" = .true., ignored otherwise)
   +--------------------------------------------------------------------
   
```
