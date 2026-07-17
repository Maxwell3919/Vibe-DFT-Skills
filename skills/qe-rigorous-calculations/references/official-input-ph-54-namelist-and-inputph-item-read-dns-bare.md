# INPUT_PH — NAMELIST: &INPUTPH — Item: read_dns_bare

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `c70823ec958777e86e9fd8affa11dd8230c7c2ac46318e98b2e4ba3b0b88cd9d`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


read_dns_bare

LOGICAL

Default:

.false.

If .true. the PH code tries to read three files in the DFPT+U
calculation: dns_orth, dns_bare, d2ns_bare.
dns_orth and dns_bare are the first-order variations of
the occupation matrix, while d2ns_bare is the second-order
variation of the occupation matrix. These matrices are
computed only once during the DFPT+U calculation. However,
their calculation (especially of d2ns_bare) is computationally
expensive, this is why they are written to file and then can be
read (e.g. for restart) in order to save time.

[
Back to Top
]
```
