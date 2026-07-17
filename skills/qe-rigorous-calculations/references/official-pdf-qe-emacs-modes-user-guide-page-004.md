# qe_emacs_modes_user_guide.pdf — page 4

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/qe_emacs_modes_user_guide.pdf
- Retrieved: 2026-07-17T11:53:48+00:00
- Official source SHA-256: `13d904bbd6efc960f111b319f0565aab6bd8046f038eee0e128ffa4a20f1f8e8`
- Extracted text SHA-256: `894ec6bfd3bd4c2eb6e4b8ae1ab477634e9bc4c2233898fbebb84cea113ae481`
- Official Last-Modified: Mon, 08 Dec 2025 21:50:22 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    (add-to-list 'auto-mode-alist              '("/pw.*\\.in\\'" . pw-mode))
    (add-to-list 'auto-mode-alist              '("/scf.*\\.in\\'" . pw-mode))
    (add-to-list 'auto-mode-alist              '("/relax.*\\.in\\'" . pw-mode))
    (add-to-list 'auto-mode-alist              '("/vc-relax.*\\.in\\'" . pw-mode))

    ;; automatically open the neb*.in files with neb.x mode
    (add-to-list 'auto-mode-alist '("/neb.*\\.in\\'" . neb-mode))

    ;; automatically open the cp*.in files with cp.x mode
    (add-to-list 'auto-mode-alist '("/cp.*\\.in\\'" . cp-mode))

    ;; automatically open the ph*.in files with ph.x mode
    (add-to-list 'auto-mode-alist '("/ph.*\\.in\\'" . ph-mode))

    ;; automatically open the pp*.in files with pp.x mode
    (add-to-list 'auto-mode-alist '("/pp.*\\.in\\'" . pp-mode))

Beware that the more general *.in pattern for the generic qe-mode1 should be specified first
or else any *.in file will be recognized as generic QE input file.
    For those who are fans of regular-expressions, the above four lines for pw-mode can be
expressed by the following one-liner:
    (add-to-list 'auto-mode-alist '("/\\(pw\\|scf\\|\\(?:vc-\\)?relax\\).*\\.in\\'" . pw-mode))

If we want that emacs opens *.pwtk files in the PWTK QE mode, we can use:

    ;; automatically open the *.pwtk files with the PWTK mode
    (add-to-list 'auto-mode-alist '("\\.pwtk\\'" . pwtk-mode))

   Once the package is installed according to the above instructions, we are ready to use it.
Let us, for the sake of example, open an existing pw.x input file whose name does not match
the above specified filename pattern for the pw-mode. In such cases we can load the mode with
M-x pw-mode command and we will get the content of the file highlighted as in Figure 1.


4     Usage
4.1     Available modes defined by qe-modes
The QE-modes package contains a generic qe-mode and the following specific modes: pw-mode,
neb-mode, cp-mode, ph-mode, ld1-mode, and pp-mode. The difference between them is only in
the extent of the syntax highlighting and auto-indentation. Namely, these modes recognize and
highlight namelists (and their variables) and cards (and their options/flags) that they know
about. The generic qe-mode is aware of all of them for all those Quantum ESPRESSO
programs that have explicit documentation in the form of INPUT_PROG .html files (where PROG
typically stands for the uppercase name of the program). In contrast, a given specific mode is
aware only of namelists, variables, cards, and options of the corresponding program.
   1
     Please note the difference between qe-modes and qe-mode: the first implies the whole package, whereas the
second means the generic QE mode, which is only one among the available modes in the qe-modes package.



                                                      4
```
