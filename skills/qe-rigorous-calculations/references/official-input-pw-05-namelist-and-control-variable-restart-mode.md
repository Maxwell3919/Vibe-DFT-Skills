# INPUT_PW — NAMELIST: &CONTROL — Variable: restart_mode

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `892a1d8bf4511cbc96b7dac9c114c5036080626ced840ed0e3d8bbc2db5d58e4`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       restart_mode
   
   Type:           CHARACTER
   Default:        'from_scratch'
   Description:   
                   Available options are:
    
                   'from_scratch' :
                        From scratch. This is the normal way to perform a PWscf calculation
    
                   'restart' :
                        From previous interrupted run. Use this switch only if you want to
                        continue, using the same number of processors and parallelization,
                        an interrupted calculation. Do not use to start a new one, or to
                        perform a non-scf calculations.  Works only if the calculation was
                        cleanly stopped using variable "max_seconds", or by user request
                        with an "exit file" (i.e.: create a file "prefix".EXIT, in directory
                        "outdir"; see variables "prefix", "outdir"). The default for
                        "startingwfc" and "startingpot" is set to 'file'.
   +--------------------------------------------------------------------
   
```
