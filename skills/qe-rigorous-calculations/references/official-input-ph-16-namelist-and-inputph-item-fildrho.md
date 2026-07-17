# INPUT_PH — NAMELIST: &INPUTPH — Item: fildrho

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `05c2608060abfdf20634577003a87e27da0efd5f432167ef9000054f5fc4053c`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


fildrho

CHARACTER

Default:

' '

File where the charge density responses are written. Note that the file
will actually be saved as 
${outdir}/_ph0/${prefix}.${fildrho}1

where 
${outdir},

${prefix}
and 
${fildrho}
are the values of the
corresponding input variables

[
Back to Top
]
```
