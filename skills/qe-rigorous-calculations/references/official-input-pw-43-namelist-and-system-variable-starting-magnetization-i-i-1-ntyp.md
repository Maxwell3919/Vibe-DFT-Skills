# INPUT_PW — NAMELIST: &SYSTEM — Variable: starting_magnetization(i), i=1,ntyp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `e89894564e662a6cccf0165da4ba20d6221f8206577cc1f836211418259d3f63`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       starting_magnetization(i), i=1,ntyp
   
   Type:           REAL
   Default:        0
   Description:    Starting spin polarization on atomic type 'i' in a spin-polarized
                   (LSDA or non-collinear/spin-orbit) calculation.
                   The input values can have an absolute value greater than or equal to 1,
                   which will be interpreted as the site's magnetic moment.
                   Alternatively, the values can range between -1 and 1,
                   which will be interpreted as the site magnetization per valence electron.
                   For QE-v7.2 and older versions, only the second option is allowed.
                   
                   If you expect a nonzero magnetization in your ground state,
                           you MUST either specify a nonzero value for at least one
                           atomic type, or constrain the magnetization using variable
                           "tot_magnetization" for LSDA, "constrained_magnetization"
                           for noncollinear/spin-orbit calculations. If you don't,
                           you will get a nonmagnetic (zero magnetization) state.
                   In order to perform LSDA calculations for an antiferromagnetic
                           state, define two different atomic species corresponding to
                           sublattices of the same atomic type.
                   
                   NOTE 1: "starting_magnetization" is ignored in most BUT NOT ALL
                           cases in non-scf calculations: it is safe to keep the same
                           values for the scf and subsequent non-scf calculation.
                   
                           NOTE 2: If you fix the magnetization with
                           "tot_magnetization", do not specify "starting_magnetization".
                   
                           NOTE 3: In the noncollinear/spin-orbit case, starting with zero
                   starting_magnetization on all atoms imposes time reversal
                   symmetry. The magnetization is never calculated and is
                           set to zero (the internal variable domag is set to .FALSE.).
   +--------------------------------------------------------------------
   
```
