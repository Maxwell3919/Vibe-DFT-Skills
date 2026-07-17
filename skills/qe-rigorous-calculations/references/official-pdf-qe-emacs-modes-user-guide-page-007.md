# qe_emacs_modes_user_guide.pdf — page 7

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/qe_emacs_modes_user_guide.pdf
- Retrieved: 2026-07-17T11:53:48+00:00
- Official source SHA-256: `13d904bbd6efc960f111b319f0565aab6bd8046f038eee0e128ffa4a20f1f8e8`
- Extracted text SHA-256: `93bc1abe1e369cd949b5613feca955611d2545c4621ace6c10325e95d59b8cc0`
- Official Last-Modified: Mon, 08 Dec 2025 21:50:22 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
4.3.1   Selection of card’s flag value
Another available completion is the selection of the card’s flag value. For example, by typing:

   M-x pw-K\_P[space][enter]

the following list of possible values for the K_POINTS’s flag appears:

  Select the flag:      {tpiba | automatic | crystal | gamma | ...}.

The currently active value is written in bold; to use it press [enter], whereas to select another
value use the right (→) or left (←) arrow keys.

4.4     Controlling indentation
The basic indentation offset in qe-modes is 3. It is controlled by qe-indent variable. Hence if
you want to change it, add the following into your user-init-file (e.g. $HOME/.emacs):

   (setq qe-indent myOffset )

where myOffset is the integer value of the offset of your choice. For no indentation, set the
qe-indent to 0 (this implies that auto-indentation will make all lines non-indented).
   To disable the auto-indentation for a given mode (are you really sure you want to do this),
add the following into your user-init-file:

   (add-hook 'mode -mode (lambda () (setq indent-line-function 'indent-relative)))

where mode is qe, pw, neb, cp, ph, ld1, or pp.

4.5     Note to Vi users
A simple way to get a QE-modes aware Vi-compatible editor is to use the Evil package – an
extensible vi layer for Emacs (https://bitbucket.org/lyro/evil/wiki/Home). With the
Evil mode enabled, Emacs will behave like the Vi editor, but with the QE-modes support.




                                                 7
```
