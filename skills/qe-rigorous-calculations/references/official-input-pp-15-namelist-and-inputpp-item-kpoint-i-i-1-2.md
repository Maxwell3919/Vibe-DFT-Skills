# INPUT_PP — NAMELIST: &INPUTPP — Item: kpoint(i), i=1,2

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PP.html
- Retrieved: 2026-07-17T11:49:40+00:00
- Official source SHA-256: `482dc70016a4638b18eca0219e56754e09fa195524a55decd6df3e6fbc5efd1c`
- Extracted text SHA-256: `fb73cea5b3ad18ac44e3e852e652ac94be1fd71a206a6beb70776e5a11f3ae85`
- Official Last-Modified: Tue, 09 Dec 2025 07:41:05 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


kpoint(i), i=1,2

INTEGER

Unpolarized and noncollinear case:
k-point(s) to be plotted
LSDA:
k-point(s) and spin polarization to be plotted
(spin-up and spin-down correspond to different k-points!)

To plot a single kpoint ikpt, specify kpoint=ikpt or kpoint(1)=ikpt
To plot a range of kpoints [imin, imax], specify kpoint(1)=imin and kpoint(2)=imax

[
Back to Top
]
```
