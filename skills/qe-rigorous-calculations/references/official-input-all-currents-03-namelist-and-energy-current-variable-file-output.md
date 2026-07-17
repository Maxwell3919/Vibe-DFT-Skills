# INPUT_ALL_CURRENTS — NAMELIST: &ENERGY_CURRENT — Variable: file_output

- Official source: https://www.quantum-espresso.org/Doc/INPUT_ALL_CURRENTS.txt
- Retrieved: 2026-07-17T11:48:53+00:00
- Official source SHA-256: `946599588fb07aee90e335384fccef11dacc6f7103defaed914bb052eb954434`
- Extracted text SHA-256: `6ea5d93bf210d40c5e6dc2b9527fc6836a6d9dd6dca7bcc51a420688b0ce3026`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       file_output
   
   Type:           CHARACTER
   Default:        'current_hz'
   Description:    The program will write the output in "file_output" and "file_output"  + '.dat'.
                   In the latter file the format of the output is:
                   
                      NSTEP t_ps J_x J_y J_z Jele_x Jele_y Jele_z v_cm(1)_x v_cm(1)_y v_cm(1)_z ...
                   
                   where J_x, J_y, J_z are the three components of the DFT energy current,
                   and can be easily post-processed by other external programs.
                   Jele_* are the components of the electronic density current that may be used
                   for decorrelation and better data analysis or for calculating the electric current.
                   v_cm(1) ... v_cm(nsp) are the center of mass velocities for each atomic species.
                   
                   If "n_repeat_every_step" > 1, an additional file "file_output" + '.stat' is
                   written with the following format:
                   
                      NSTEP t_ps mean(J_x) mean(J_y) mean(J_z) std(J_x) std(J_y) std(J_z)
                   
                   only one line per step is printed in this case (in the other output files you will
                   find every calculation, also repeated ones). std is the standard deviation.
   +--------------------------------------------------------------------
   
```
