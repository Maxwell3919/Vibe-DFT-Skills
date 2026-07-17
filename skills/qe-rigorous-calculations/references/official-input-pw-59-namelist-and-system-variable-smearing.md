# INPUT_PW — NAMELIST: &SYSTEM — Variable: smearing

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `f9b59c25fb84697f84c9daf404a1aa580a34a9548a4ff63b6680e720dda6072b`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       smearing
   
   Type:           CHARACTER
   Default:        'gaussian'
   Description:   
                   Available options are:
    
                   'gaussian', 'gauss' :
                        ordinary Gaussian spreading (Default)
    
                   'methfessel-paxton', 'm-p', 'mp' :
                        Methfessel-Paxton first-order spreading
                        (see PRB 40, 3616 (1989)).
    
                   'marzari-vanderbilt', 'cold', 'm-v', 'mv' :
                        Marzari-Vanderbilt-DeVita-Payne cold smearing
                        (see PRL 82, 3296 (1999))
    
                   'fermi-dirac', 'f-d', 'fd' :
                        smearing with Fermi-Dirac function
   +--------------------------------------------------------------------
   
```
