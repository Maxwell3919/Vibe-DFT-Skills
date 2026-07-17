# 4.3 Band structure, Fermi surface

- Official source: https://www.quantum-espresso.org/Doc/pp_user_guide/node8.html
- Retrieved: 2026-07-17T11:52:25+00:00
- Official source SHA-256: `3f76ca4e6def7123c8ebb4c3828450f834af388cc418aa675e04c37b34a9b827`
- Extracted text SHA-256: `5c7c4164e4637196681016103ba1ff2a5962440bc09e183a3d4de0739ef4e124`
- Official Last-Modified: Mon, 08 Dec 2025 21:39:56 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.4 Projection over atomic states,

Up:

4 Usage

Previous:

4.2 About Bader's analysis

  

Contents

4.3 Band structure, Fermi surface

The code 
bands.x
reads data file(s), extracts eigenvalues,
regroups them into bands (the algorithm used to order bands and to resolve
crossings may not work in all circumstances, though). The output is written
to a file in a simple format that can be directly read and converted to
plottable format by auxiliary code

plotband.x
. Unpredictable plots may results if k-points are not 
in sequence along lines, or if two consecutive points are the same. 
The code 
bands.x
performs as well a 
symmetry analysis of the band structure. For a complete input description,
see 
Doc/INPUT_bands.*
. See Example 01, Example 04 and Example 06 
for simple band plots.

The plotting of Fermi surfaces can be performed using code 
fs.x
.
The resulting file in .bxsf format can be read and plotted
using XCrySDen. See Example 02 for an example of Fermi surface 
visualization (Ni, including the spin-polarized case).
```
