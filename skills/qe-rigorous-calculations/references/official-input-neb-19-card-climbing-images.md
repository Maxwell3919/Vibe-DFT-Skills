# INPUT_NEB — CARD: CLIMBING_IMAGES

- Official source: https://www.quantum-espresso.org/Doc/INPUT_NEB.txt
- Retrieved: 2026-07-17T11:49:26+00:00
- Official source SHA-256: `7c9f7e082b4846135e360fb86c0ce8a43f8e63825fa7d7fafcda3836a6088706`
- Extracted text SHA-256: `0c982ff18f95569b6d2a6a14869d1983cc18b5a81866494c08d25dbf2eec3447`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      CARD: CLIMBING_IMAGES 
      
         OPTIONAL CARD, NEEDED ONLY IF "CI_SCHEME" == 'MANUAL', IGNORED OTHERWISE !
         
         /////////////////////////////////////////
         // Syntax:                             //
         /////////////////////////////////////////
         
            CLIMBING_IMAGES 
               index1, index2, ... indexN
         
         /////////////////////////////////////////
         
         DESCRIPTION OF ITEMS:
         
            +--------------------------------------------------------------------
            Variables:      index1, index2, ... indexN
            
            Type:           INTEGER
            Description:    index1, index2, ..., indexN are indices of the images to which the
                            Climbing-Image procedure apply. If more than one image is specified
                            they must be separated by a comma.
            +--------------------------------------------------------------------
            
            
      ===END OF CARD==========================================================
      
      
   ### END OF SUPERCARD :  BEGIN_PATH_INPUT/END_PATH_INPUT ################
   
   
   ########################################################################
   | SUPERCARD: BEGIN_ENGINE_INPUT/END_ENGINE_INPUT
   | this supercard is enclosed within the keywords:
   |
   | BEGIN_ENGINE_INPUT
   |    ... content of the supercard here ...
   | END_ENGINE_INPUT
   |
   | The syntax of supercard's content follows below:
   
      Here comes the pw.x specific namelists and cards (see file: "" or INPUT_PW.txt)
      with the exception of "ATOMIC_POSITIONS" cards, which are specified separately within the
      "BEGIN_POSITIONS"/END_POSITIONS supercard as described below.
      
      So the input that follows here is of the following structure:
      
         &CONTROL
            ...
         /
         &SYSTEM
           ...
         /
         &ELECTRONS
           ...
         /
         ...
      
      ########################################################################
      | SUPERCARD: BEGIN_POSITIONS/END_POSITIONS
      | this supercard is enclosed within the keywords:
      |
      | BEGIN_POSITIONS
      |    ... content of the supercard here ...
      | END_POSITIONS
      |
      | The syntax of supercard's content follows below:
      
         NB:
         Atomic positions for all the images are specified within the "BEGIN_POSITIONS" / END_POSITIONS
         supercard, where each instance of "ATOMIC_POSITIONS" card is prefixed either by "FIRST_IMAGE",
         "INTERMEDIATE_IMAGE", or "LAST_IMAGE" keywords.
         IF "lfcp" == .TRUE., total charges for all images have to be specified with "TOTAL_CHARGE" cards.
         
         Note that intermediate images are optional, i.e., there can be none or any number of
         "INTERMEDIATE_IMAGE" images.
         
         ########################################################################
         | SUPERCARD: FIRST_IMAGE
         | this supercard starts with the keyword:
         |
         | FIRST_IMAGE
         |    ... content of the supercard here ...
         |
         | The syntax of supercard's content follows below:
         
            ========================================================================
```
