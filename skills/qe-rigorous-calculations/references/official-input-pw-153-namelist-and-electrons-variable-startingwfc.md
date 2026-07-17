# INPUT_PW — NAMELIST: &ELECTRONS — Variable: startingwfc

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `b771f2dc5df03e79dfdcc3f2b5e5d8f089f6e01dff8af88b5bee164f3686c2b1`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       startingwfc
   
   Type:           CHARACTER
   Default:        'atomic+random'
   Description:   
                   Available options are:
    
                   'atomic' :
                        Start from superposition of atomic orbitals.
                        If not enough atomic orbitals are available,
                        fill with random numbers the remaining wfcs
                        The scf typically starts better with this option,
                        but in some high-symmetry cases one can "loose"
                        valence states, ending up in the wrong ground state.
    
                   'atomic+random' :
                        As above, plus a superimposed "randomization"
                        of atomic orbitals. Prevents the "loss" of states
                        mentioned above.
    
                   'random' :
                        Start from random wfcs. Slower start of scf but safe.
                        It may also reduce memory usage in conjunction with
                        "diagonalization"='cg'.
    
                   'file' :
                        Start from an existing wavefunction file in the
                        directory specified by variables "prefix" and "outdir".
   +--------------------------------------------------------------------
   
```
