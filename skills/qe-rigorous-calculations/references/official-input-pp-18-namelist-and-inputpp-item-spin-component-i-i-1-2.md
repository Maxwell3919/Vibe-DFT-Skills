# INPUT_PP — NAMELIST: &INPUTPP — Item: spin_component(i), i=1,2

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PP.html
- Retrieved: 2026-07-17T11:49:40+00:00
- Official source SHA-256: `482dc70016a4638b18eca0219e56754e09fa195524a55decd6df3e6fbc5efd1c`
- Extracted text SHA-256: `bdc221b808358988f975b503e13e86f33563c51074ef034276b2166f24966cd3`
- Official Last-Modified: Tue, 09 Dec 2025 07:41:05 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


spin_component(i), i=1,2

INTEGER

Default:

0

Status:

OPTIONAL

Noncollinear case only:

plot the contribution of the given state(s) to the charge
or to the magnetization along the direction(s) indicated
by spin_component:
0 = charge (default),
1 = x,
2 = y,
3 = z.

Ignored in unpolarized or LSDA case

To plot a single component ispin, specify spin_component=ispin or spin_component(1)=ispin
To plot a range of components [imin, imax], specify spin_component(1)=imin and spin_component(2)=imax

[
Back to Top
]

ELSEIF 
plot_num=10
:

Options for ILDOS (plot_num=10):
```
