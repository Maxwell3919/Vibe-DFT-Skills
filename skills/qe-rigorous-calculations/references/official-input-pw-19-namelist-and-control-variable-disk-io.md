# INPUT_PW — NAMELIST: &CONTROL — Variable: disk_io

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `e4228a46f9367787436723623a0b28605736c47780e769c95376513c9066faa2`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       disk_io
   
   Type:           CHARACTER
   Default:        see below
   Description:   
                   Specifies the amount of disk I/O activity:
                   (only for binary files and xml data file in data directory;
                   other files printed at each molecular dynamics / structural
                   optimization step are not controlled by this option )
    
                   'high' :
                        save charge to disk at each SCF step,
                        keep wavefunctions on disk (in "distributed" format),
                        save mixing data as well.
                        Do not use this option unless you have a good reason!
                        It is no longer needed to specify 'high' in order to be able
                        to restart from an interrupted calculation (see "restart_mode")
    
                   'medium' :
                        save charge to disk at each SCF step,
                        keep wavefunctions on disk only if more than one k-point,
                        per process is present, otherwise keep them in memory;
                        save them to disk only at the end (in "portable" format)
    
                   'low' :
                        save charge to disk at each SCF step,
                        keep wavefunctions in memory (for all k-points),
                        save them to disk only at the end (in "portable" format).
                        Reduces I/O but increases memory wrt the previous cases
    
                   'nowf' :
                        save to disk only the xml data file and the charge density
                        at convergence, never save wavefunctions. Restarting from
                        an interrupted calculation is not possible with this option.
    
                   'minimal' :
                        save to disk only the xml data file at convergence
    
                   'none' :
                        do not save anything to disk
    
                   Default is 'low' for the scf case, 'medium' otherwise.
                   Note that the needed RAM increases as disk I/O decreases
   +--------------------------------------------------------------------
   
```
