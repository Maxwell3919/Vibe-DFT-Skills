# INPUT_PPACF — NAMELIST: &PPACF — Variable: code_num

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PPACF.txt
- Retrieved: 2026-07-17T11:49:41+00:00
- Official source SHA-256: `ec18cfa677f3d5684e7176a867c5d56868b44758bd2d43678d4ee813e1ecfc39`
- Extracted text SHA-256: `4d6783de88a0d274b1d01bae3022c46e0ee4705a8be995b7accd4363cfbffa85`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       code_num
   
   Type:           INTEGER
   Description:    Select from which code to read output files.
                     1 = Quantum ESPRESSO
                     2 = VASP
                         The codes will read vasprun.xml and CHGCAR from VASP
                         calculations.
                         Please note that in VASP-based analysis:
                         - Core charge is ignored.
                         - The ppacf-from-VASP-read-in only works for VASP
                           calculations done in PBE, revPBE, vdW-DF, vdW-DF2, or vdW-DF-cx
                         - The ppacf-from-VASP-read-in only always uses the full Ecnl kernel
                           for coupling-constant scaling analysis of vdW-DF versions.
                         - Wavefunction based analysis (Fock exchange energy and
                           Kohn-Sham kinetic energy) are not available from VASP
                         - When "lplot" = .True., the code will also print out
                           charge density in prefix.chg (prefix.chg1 and prefix.chg2
                           save the spin-up and spin-down components in case of
                           spin-polarized calculations), which can be processed by pp.x.
   Default:        1
   +--------------------------------------------------------------------
   
```
