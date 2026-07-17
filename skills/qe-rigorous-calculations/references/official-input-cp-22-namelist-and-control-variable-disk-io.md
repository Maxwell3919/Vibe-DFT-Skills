# INPUT_CP — NAMELIST: &CONTROL — Variable: disk_io

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `c737bba930cd3c609df8a2a4f16a902ee643ccae347a6bdfd53c071ed733be4b`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       disk_io
   
   Type:           CHARACTER
   Default:        'default'
   Description:    'high': CP code will write Kohn-Sham wfc files and additional
                           information in data-file.xml in order to restart
                           with a PW calculation or to use postprocessing tools.
                           If disk_io is not set to 'high', the data file
                           written by CP will not be readable by PW or PostProc.
   +--------------------------------------------------------------------
   
```
