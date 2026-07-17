# INPUT_OSCDFT_ET — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_OSCDFT_ET.txt
- Retrieved: 2026-07-17T11:49:29+00:00
- Official source SHA-256: `cc118445191526650730ffd03159437d060d974a4a8977f99da032918b290890`
- Extracted text SHA-256: `e0bd9b69f18942941bd6dde997ebb8d382f468986ae9137ab529079601acc8b7`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:26 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: oscdft_et.x / PWscf / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Input data format: { } = optional, [ ] = it depends, | = or

Purpose of oscdft_et.x:
This calculates the electronic coupling of an electron transfer process.
This requires two scf calculations:
- one calculation has the system constrained to its initial state and,
- the other calculation has the system constrained to its final state,
with both calculation using the same atomic positions.
The transferring electron is constrained to the donor atom in the initial state
while it is constrained to the acceptor atom in the final state.

Structure of the input data:
===============================================================================

    &OSCDFT_ET_NAMELIST
      ...
    /



========================================================================
```
