# 4.4 DFPT with the tetrahedron method

- Official source: https://www.quantum-espresso.org/Doc/ph_user_guide/node11.html
- Retrieved: 2026-07-17T11:51:36+00:00
- Official source SHA-256: `8a0cfa59d3633d73081fa6a23699f351e587269410e6d32ec1a0e136d7e87392`
- Extracted text SHA-256: `a24fe33961701dd70358b6f22280a3aa99b437b09304fff577325c9f651ca132`
- Official Last-Modified: Tue, 14 Oct 2025 10:25:49 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.5 Calculation of electron-phonon interaction

Up:

4 Using PHonon

Previous:

4.3 Calculation of electron-phonon interaction

  

Contents

4.4 DFPT with the tetrahedron method

In order to use the tetrahedron method for phonon calculations,
you should run 
pw.x
and 
ph.x
as follows:

Run 
pw.x
with 
occupation = "tetrahedra_opt"
and 
K_POINT automatic
.

Run 
ph.x
.

There is an example in 
PHonon/example/tetra_example/
.
```
