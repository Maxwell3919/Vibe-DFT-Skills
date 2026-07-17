# INPUT_ALL_CURRENTS — NAMELIST: &ENERGY_CURRENT — Variable: n_repeat_every_step

- Official source: https://www.quantum-espresso.org/Doc/INPUT_ALL_CURRENTS.txt
- Retrieved: 2026-07-17T11:48:53+00:00
- Official source SHA-256: `946599588fb07aee90e335384fccef11dacc6f7103defaed914bb052eb954434`
- Extracted text SHA-256: `1aab47f05d47f3d370df1de21232130788b0cedf47eb92d7148dcd185def2d8e`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       n_repeat_every_step
   
   Type:           INTEGER
   Default:        1
   Description:    Number of repetition of the full current calculation for each step. If > 1, the file "file_output" + '.stat'
                   is written with some statistics. Note that if you don't specify at least "re_init_wfc_1" ,this may be useless.
                   You may want to specify startingwfc = 'random' in the ELECTRONS namelist.
   +--------------------------------------------------------------------
   
```
