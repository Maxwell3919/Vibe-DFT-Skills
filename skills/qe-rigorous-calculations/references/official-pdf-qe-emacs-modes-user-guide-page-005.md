# qe_emacs_modes_user_guide.pdf — page 5

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/qe_emacs_modes_user_guide.pdf
- Retrieved: 2026-07-17T11:53:48+00:00
- Official source SHA-256: `13d904bbd6efc960f111b319f0565aab6bd8046f038eee0e128ffa4a20f1f8e8`
- Extracted text SHA-256: `913f7dfb9515f26a884e02c713827f5480b9badf2b748aa1f94c100db62d0098`
- Official Last-Modified: Mon, 08 Dec 2025 21:50:22 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
Figure 2: The result of executing the M-x pp-insert-template command, which insert a
template for the pp.x input file into the current buffer.

4.2    Commands
The QE-modes package provides the following commands:
• M-X mode -mode
     toggles the respective mode, where mode is one of qe, pw, neb, cp, ph, ld1, or pp
• M-x indent-region or C-M-\
     indents region according to qe-modes rules, i.e., namelist and card names are left aligned
     to the first column, while their content is indented by qe-indent spaces to the right (see
     Figure 1; default value of qe-indent is 3)
• M-x prog -insert-template
     inserts a respective input file template (see Figure 2); this command may not be defined
     for all the prog s; currently supported prog s are: pw, cp, pp, neb, ph, dynmat, ld1,
     projwfc, dos, and bands.
• M-x prog-NAMELIST
     inserts a blank namelist section named NAMELIST

                                              5
```
