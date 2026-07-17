# INPUT_CP — NAMELIST: &CELL — Variable: cell_dynamics

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `ffa81e8136708b19ba5a14c18991744f172d18893782523e7f91e63b05163d30`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       cell_dynamics
   
   Type:           CHARACTER
   Default:        'pr'      if "calculation" = 'vc-md', 'vc'cp', 'vc-cp-wf';
                                        'damp-pr' if  "calculation" = 'vc-relax';
                                        'none'    otherwise
   Description:    set how cell should be moved
                   'none'      : cell is kept fixed
                   'sd'        : steepest descent algorithm is used to optimise the
                                 cell
                   'damp-pr'   : damped dynamics is used to optimise the cell
                                 ( Parrinello-Rahman method ).
                   'pr'        : standard Verlet algorithm is used to propagate
                                 the cell ( Parrinello-Rahman method ).
   +--------------------------------------------------------------------
   
```
