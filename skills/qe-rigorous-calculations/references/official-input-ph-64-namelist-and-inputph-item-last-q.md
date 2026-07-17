# INPUT_PH — NAMELIST: &INPUTPH — Item: last_q

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `56f69c56e6281ceb931068087167a86a2c85db82a982bd92691ecd41b9f3962a`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


last_q

INTEGER

Default:

number of q points

See:

start_q

Used only when 
ldisp
=.true..
Computes only the q points from 
start_q
to 
last_q
.

IMPORTANT
* 
last_q
must be <= 
nqs
(number of q points)
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
