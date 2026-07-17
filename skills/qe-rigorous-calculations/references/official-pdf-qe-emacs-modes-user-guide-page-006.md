# qe_emacs_modes_user_guide.pdf — page 6

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/qe_emacs_modes_user_guide.pdf
- Retrieved: 2026-07-17T11:53:48+00:00
- Official source SHA-256: `13d904bbd6efc960f111b319f0565aab6bd8046f038eee0e128ffa4a20f1f8e8`
- Extracted text SHA-256: `fff0df4041648e7d8cdd32ac328cfb88567bcac8af40fb546512cdfb007042be`
- Official Last-Modified: Mon, 08 Dec 2025 21:50:22 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
• M-x prog-CARD
     inserts a blank card section named CARD ; the value of the card’s flag can be selected
     from the provided list by using the right/left arrow keys
• M-x prog-variable
     inserts a namelist variable named variable
The above italicized words have the following meaning:
      • prog stands for the lowercase name of respective program without the .x suffix (i.e. it is
        the lowercase variant of the PROG in the respective INPUT PROG .html filename)
      • NAMELIST is the uppercase name for a given Fortran namelist
      • CARD is the uppercase name for a given card
      • variable is the lowercase name for a given namelist’ variable
Note that in the above commands the spelling of namelist and card names (NAMELIST and
CARD ) are intentionally made uppercase as to differentiate them from the names of variables
which are intentionally made lowercase.2

4.3      Auto-completion mechanism
It may at first seem that the above described commands are not a big deal. But given that
Quantum ESPRESSO contains hundreds of variables it is difficult to remember the precise
spelling for all of them. It is here where these commands becomes useful due to Emacs auto-
completion mechanism. For example, typing a space or tab after M-x pw-C prints all the
namelists and cards that starts with letter “C”, i.e.:
      Possible completions are:
      pw-CELL                                          pw-CELL_PARAMETERS
      pw-CONSTRAINTS                                   pw-CONTROL
whereas typing a space or tab after M-x pw-c prints all the pw.x variables that starts with
letter “c”, i.e.:
      Possible completions are:
      pw-c                                             pw-calculation
      pw-cell_dofree                                   pw-cell_dynamics
      pw-cell_factor                                   pw-celldm
      pw-constrained_magnetization                     pw-conv_thr
      pw-conv_thr_init                                 pw-conv_thr_multi
      pw-cosab                                         pw-cosac
      pw-cosbc
From this list we can see that there is only one variable that starts with “ca”, hence typing M-x
pw-ca[space][return], where [space][return] stands for space and return keys, prints at
the point position of the current buffer:
      calculation = ''
  2
    Note that in Quantum ESPRESSO the namelist and variable names are case-insensitive, while card names
are case-sensitive.

                                                   6
```
