# 4.2 About Bader's analysis

- Official source: https://www.quantum-espresso.org/Doc/pp_user_guide/node7.html
- Retrieved: 2026-07-17T11:52:24+00:00
- Official source SHA-256: `2d6f9cdf5eecd981d5f77e6c922347ff484125fb6c3f3da7087651ae59be4cae`
- Extracted text SHA-256: `70c7023e5c8592794583ed4318db2c2406c08e1903bc6fef5227392ab48f612d`
- Official Last-Modified: Mon, 08 Dec 2025 21:39:56 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.3 Band structure, Fermi surface

Up:

4 Usage

Previous:

4.1 Plotting selected quantities

  

Contents

4.2 About Bader's analysis

In 
http://theory.cm.utexas.edu/henkelman/code/bader/

one can find a software that performs Bader's analysis starting 
from charge on a regular grid. One should use PAW to compute the
charge density. The required "cube" format can be produced using 

pp.x
(info by G. Lapenna who has successfully used this 
technique, but adds: ``Problems occur with polar X-H bonds or in
all cases where the zero-flux of density comes too close to atoms 
described with pseudo-potentials"). This code should perform 
decomposition into Voronoi polyhedra as well, in place of obsolete
code 
voronoy.x
(removed from distribution since v.4.2).
Alternatively, you can use 
CRITIC2
, available at

https://github.com/aoterodelaroza/critic2
, which can
read directly 
pw.x
output and ``XSF'' files. 
CRITIC2

functionaly include Bader's AIM, ELF, laplacian of density and
potentials, non-covalente interaction (NCI) plots and much more.
```
