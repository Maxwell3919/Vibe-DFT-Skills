# 4.5 Color plot of the Fermi velocity and the orbital character on Fermi surfaces

- Official source: https://www.quantum-espresso.org/Doc/pp_user_guide/node10.html
- Retrieved: 2026-07-17T11:52:09+00:00
- Official source SHA-256: `9921d9cf05862c0846b239e5d458072e6df85729306a4d3ce93143453ca3fc40`
- Extracted text SHA-256: `32e4a86629aa42f175a5c0617a08ed7fbcbaa12eccdd8082972bcc91148f96fb`
- Official Last-Modified: Mon, 08 Dec 2025 21:39:56 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.6 Wannier functions

Up:

4 Usage

Previous:

4.4 Projection over atomic states,

  

Contents

4.5 Color plot of the Fermi velocity and the orbital character
on Fermi surfaces

You can plot any quantity on Fermi surfaces as a color plot 
by using 
fermisurfer
program
1
.

fermi_velocity.x
and 
fermi_proj.x
are used 
to generate an input file for 
fermisurfer
from the output
of 
pw.x
or 
projwfc.x
.

fermi_velocity.x
generates a color-plot of Fermi velocity.
You use it as follows:

Run 
pw.x
with 
K_POINT automatic
.

Run 

$ fermi_velocity.x -in {pw.x input file}

vfermi.frmsf
is generated

fermi_proj.x
generates a color plot of an orbital character.
You use it as follows:

Run 
pw.x
with 
K_POINT automatic
.

Run 
projwfc.x
just to generate 
{prefix}.save/atomic_proj.*
.

Run 

$ fermi_proj.x -in {input file}

Input-file format is as follows:

&PROJWFC
{The same as the input of projwfc.x}
/
{Number of target wavefunctions}
{Index of target WFC1} {Index of target WFC2} {Index of target WFC3} ...

It generates 

$\sum_{{i=1}}^{{n_{\rm target}}}$ 
|〈
$\varphi_{{{\rm target}(i)}}^{{\rm atom}}$ 
|
$\varphi_{{n k}}^{}$ 
〉|
2
, 
where 
n
s
and 

target
(
i
) are
the number of the target wavefunctions
and the indices of target wavefunctions, respectively.

The above quantity is written into 
"proj.frmsf"
,
which can be read by FermiSurfer program.

There is an example of 
fermi_velocity.x
and 
fermi_proj.x

in 
fermisurf_example/
.
```
