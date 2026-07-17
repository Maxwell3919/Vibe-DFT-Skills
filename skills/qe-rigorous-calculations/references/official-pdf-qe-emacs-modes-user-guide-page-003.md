# qe_emacs_modes_user_guide.pdf — page 3

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/qe_emacs_modes_user_guide.pdf
- Retrieved: 2026-07-17T11:53:48+00:00
- Official source SHA-256: `13d904bbd6efc960f111b319f0565aab6bd8046f038eee0e128ffa4a20f1f8e8`
- Extracted text SHA-256: `89e8a35a6b211cd45f432d847b68a516e8f2c5525b20829f388b751b7055b874`
- Official Last-Modified: Mon, 08 Dec 2025 21:50:22 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
3     Installation
The installation of QE-modes package consists of two parts: (i) installing the package itself and
(ii) informing Emacs about it by editing the user-init-file (typically $HOME/.emacs).

3.1    Installing the QE-modes package
Once the QE-modes-7.4.tar.gz archive is unpacked and you are located in its root directory,
the installation is trivial. Simply use:

    ./install.sh

which will install the package in the qe-modes subdirectory of the $HOME/.emacs.d/ directory
(the script copies the QE-modes *.el files to $HOME/.emacs.d/ and byte-compiles them into
*.elc files).
   If you prefer to install QE-modes into other directory, use instead:

    prefix=where-to-install ./install.sh

which will install the package in the qe-modes subdirectory of where-to-install directory.

3.2    Editing the user-init-file file
A default QE-modes snippet for user-init-file is provided by the qe-modes.emacs file
in the QE-modes source package root directory. If QE-modes were installed in default
$HOME/.emacs.d/qe-modes/ location, then the qe-modes.emacs file can be used ver-
batim; just append its content to your ~/.emacs file.
   Here is a the explanation of the simplified qe-modes.emacs file. Emacs is informed about
the installed QE-modes by the following lines in the user-init-file (e.g. $HOME/.emacs):

    ;; make sure package is visible to emacs (if needed)
    (add-to-list 'load-path "/full/path/name/of /qe-modes")

    ;; load the package
    (require 'qe-modes)

where /full/path/name/of is the directory where the qe-modes are installed (either the
$HOME/.emacs.d/ or the above where-to-install ).
   Furthermore, we can specify some filename patterns so that Emacs will automatically rec-
ognize from the filename if it is some variant of the Quantum ESPRESSO input file. Say
that we use the .in extension for the Quantum ESPRESSO input files in general and more
specifically, the pw., scf., relax., and vc-relax. prefixes for the pw.x input files and neb.,
cp., ph., and pp. prefixes for the neb.x, cp.x, ph.x, and pp.x input files. These filename
recognitions can be achieved by:

    ;; automatically open the *.in files with generic QE mode
    (add-to-list 'auto-mode-alist '("\\.in\\'" . qe-mode))

    ;; automatically open the pw*.in, scf*.in, relax*in, vc-relax*.in files
    ;; with pw.x mode

                                               3
```
