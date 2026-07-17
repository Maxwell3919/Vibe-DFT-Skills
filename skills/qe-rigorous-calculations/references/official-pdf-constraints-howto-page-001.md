# constraints_HOWTO.pdf — page 1

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/constraints_HOWTO.pdf
- Retrieved: 2026-07-17T11:53:25+00:00
- Official source SHA-256: `e0c45f7cffa1b0e6827e2b3b3590562cb7f07d472e9193f085d43330a8a2b0a6`
- Extracted text SHA-256: `e9f559509d93cf348036ab879db90195609b4eaac5606f016bc538b8c8b551a3`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
        How to implement new constraints into
                Quantum ESPRESSO
                                    Carlo Sbraccia
                                  December 8, 2025


   The two basic ingredients that are required to implement a new type of
constraint into the Quantum ESPRESSO distribution are:

       the analytical expression for the constraint σ({R3N }) (it must be a
        function of the ionic coordinates {R3N } only);

       the analytical expression for the gradients of the constraint ∇Ri σ({R3N })
        with respect to the ionic coordinates.

Given these expressions one has simply to follow what has already been done
for the standard constraint types.1 No detailed knowledge of the algorithm
used to impose the constraints (SHAKE) is necessary since the implemen-
tation is designed to work for any possible kind of constraint, provided it
is defined by an analytical expression. In the following I describe the three
basic steps that are strictly necessary to implement a new constraint type.
    One first has to modify the routine that reads the CONSTRAINTS input card
(this input card contains the parameters specified at run-time by the user to
define the constraint). The name of this routine is card constraints() and
it is located in the module Modules/read cards.f90. Note the maximum
allowed number of input parameters used to define a single constraint is 6;
if the new constraint type requires additional input parameters one has to
  1
      At present the constraint types implemented in Quantum ESPRESSO are:
       coordination numbers;
       distances;
       planar angles (linear angles included);
       torsional angles.




                                              1
```
