# INPUT_PH — NAMELIST: &INPUTPH — Item: start_irr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `a59e832085b5a6e5b9e689d389d502198aadf24bc413f054639143e2bdfd3157`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


start_irr

INTEGER

Default:

1

See:

last_irr

Perform calculations only from 
start_irr
to 
last_irr

irreducible representations.

IMPORTANT:
* 
start_irr
must be <= 3*nat
* do not specify 
nat_todo
together with

start_irr
, 
last_irr

[
Back to Top
]
```
