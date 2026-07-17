# constraints_HOWTO.pdf — page 2

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/constraints_HOWTO.pdf
- Retrieved: 2026-07-17T11:53:25+00:00
- Official source SHA-256: `e0c45f7cffa1b0e6827e2b3b3590562cb7f07d472e9193f085d43330a8a2b0a6`
- Extracted text SHA-256: `88fa574751497608541abebb81b72184f70cbf64d6eefe57e9b33727552a3014`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
modify the dimension of the array constr inp(:,:) defined in the mod-
ule Modules/input parameters.f90. All the other arrays are dynamically
allocated.
    Then one has to copy the input arrays into the internal ones (this is au-
tomatically done and should not not require any additional tuning) and to
initialise the target value of each constraint (the target corresponds to the
initial value of σi ({R3N
                       0 }; this is the quantity that is kept constant during
the simulation). All this is done in the routine init constraint() which
is located in the module Modules/constraints module.f90. One has to
define the new variables that are needed to calculate the value of the con-
straint (possibly recicling those that are already there) and then implement
the equation defining the constraint (following what is done for the other
constraint types).
    The last step consists in the implementation of the constraint’s gradient
∇σ({R3N }). This is done in the routine constraint grad() located in the
module Modules/constraints module.f90. Again one has to define the
new variables and implement the equations that define both the constraint
violation and the constraint gradients (respectively stored in g and dg(:,:)).
This is done for a single constraint σi (identified by the input variable index)
since the routine is externally called by other drivers as many times as the
number of constraints.    Note that for each constraint the sum of the gradients
                               3N
                 P
must be zero:       i ∇Ri σ({R    }) = 0. This is usually imposed by defining
one of the gradients to be equal to minus the sum of all the others.
    Finally, one should not forget to test the new constraint on both PWscf
and CP by monitoring the energy conservation and, of course, the conserva-
tion of the constraint itself.




                                       2
```
