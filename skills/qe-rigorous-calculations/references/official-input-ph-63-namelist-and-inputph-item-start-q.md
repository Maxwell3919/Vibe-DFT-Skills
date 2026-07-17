# INPUT_PH — NAMELIST: &INPUTPH — Item: start_q

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `97af4f6c69797209a59f6289f3b9b8b4526223db5908dcc27173c9a7a065f9c2`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


start_q

INTEGER

Default:

1

See:

last_q

Used only when ldisp=.true..
Computes only the q points from 
start_q
to 
last_q
.

IMPORTANT:
* 
start_q
must be <= 
nqs
(number of q points found)
* do not specify 
nat_todo
together with

start_q
, 
last_q

[
Back to Top
]
```
