# INPUT_PH — NAMELIST: &INPUTPH — Item: wpot_dir

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `2ee65304bc283cc4d771eae070255af25df2232a5cc3449fe2ccd66660a27872`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


wpot_dir

CHARACTER

Default:

outdir // 'w_pot/'

Directory where the w_pot binary files are written.
Must be the same with 
wpot_dir
used in dvscf_q2r.x.
The real space potential files are stored in 
wpot_dir

with names ${prefix}.wpot.irc${irc}//"1".

[
Back to Top
]
```
