# INPUT_CP — CARD: PLOT_WANNIER

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `8d7766dc7c8cdaf438d3eebba11404cc98a18682f3d5a7ac0628cecf77cc41c7`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: PLOT_WANNIER 

   OPTIONAL CARD, INDICES OF THE STATES THAT HAVE TO BE PRINTED (ONLY FOR CALF=1 AND CALF=5).
   
   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
      PLOT_WANNIER 
         iwf(1)    
         iwf(2)    
         . . . 
         iwf(nwf)  
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Variable:       iwf
      
      Type:           INTEGER
      Description:    These are the indices of the states that you want to output.
                      Also used with calwf = 1 and 5. If calwf = 1, then you need
                      nwf indices here (each in a new line). If CALWF=5, then just
                      one index in needed.
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


########################################################################
| SUPERCARD: AUTOPILOT/ENDRULES
| this supercard is enclosed within the keywords:
|
| AUTOPILOT
|    ... content of the supercard here ...
| ENDRULES
|
| The syntax of supercard's content follows below:

   Optional card, changes some variables on the fly of the calculation.
   
   Notice that the rules has to be ordered in with time step and the
   AUTOPILOT card has to be terminated with the ENDRULES keyword.
   
   To set up a rule, one can add the scheduled steps with on_step and
   separate the corresponding change in parameters with a column.
   
   A simple example:
   
   AUTOPILOT
       on_step =  31  : "dt"               = 5.0
       on_step =  91  : "iprint"           = 100
       on_step =  91  : "isave"            = 100
       on_step = 191  : "ion_dynamics"     = 'damp'
       on_step = 191  : "electron_damping" = 0.00
       on_step = 691  : "ion_temperature"  = 'nose'
       on_step = 691  : "tempw"            = 150.0
   ENDRULES
   
### END OF SUPERCARD :  AUTOPILOT/ENDRULES #############################


This file has been created by helpdoc utility on Wed Sep 03 14:24:03 CEST 2025
```
