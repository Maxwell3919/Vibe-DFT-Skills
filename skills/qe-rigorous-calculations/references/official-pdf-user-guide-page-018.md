# user_guide.pdf — page 18

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `83d9922452a47ef30ba0354cd22e40c74b1424f3950ea7a32767cd2df411df20`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
on the cases, therefore a good check of the chosen functionals is recommended before doing
expensive runs.
Some functionals in libxc incorporate the exchange part and the correlation one into one term
only (e.g. the ones that include the ‘ xc’ kind label in their name). In these cases the whole
functional is formally treated as ‘correlation only’ by Quantum ESPRESSO. This does not
imply any loss of information.

2.6.4   Special cases
A number of libxc functional routines need extra information on input and/or provide only
partial information on output (e.g. the energy or the potential only). In these cases the use
of such functionals may not be straightforward and, depending on the cases, may require some
work on the Quantum ESPRESSO source code.

External parameters. Several functionals in libxc depend on one or more external pa-
rameters. Some of these can be recovered inside Quantum ESPRESSO, some others are
not directly available. In all these cases a direct intervention on the Quantum ESPRESSO
source code might be necessary in order to be able to properly use such functionals. However
two routines have been defined in the XC library of Quantum ESPRESSO that ease the task
of setting and recovering the external parameters in libxc:

   • get libxc ext param: this function receives as input the ID of the libxc functional and
     the index of the chosen parameter and returns its value. If the parameter has not been
     set before it returns its default value.

   • set libxc ext param: this routine receives as input the index of the functional family-
     type (from 1 to 6: lda-exch, lda-corr, gga-exch, ...), the index of the chosen libxc param-
     eter and the value to set it to.

In order to see the available parameters for a given libxc functional and their corresponding
indexes, the xc infos.x program is available in XClib folder. For more details see Sec. 2.6.5.
The two routines can be called almost anywhere in Quantum ESPRESSO, however, as any
other XClib setting routine, they must be declared through the xc lib module.
Without setting the external parameters inside the code, their default value will be assumed.
This could lead to results different from the expectations.
In any case, when external parameters are needed by the chosen functionals, a warning message
will appear in the output of Quantum ESPRESSO. An example of Libxc parameter setting
can be found in the xclib test.f90 code (see below).

Functionals with partial output. A few libxc functional routines provides the potential
but not the energy. These functionals are available in Quantum ESPRESSO for all the
families and their output energy is set to zero.

MGGA Functionals that depend on the Laplacian of the density. At present such
functionals are formally usable in Quantum ESPRESSO , but their dependency on the
Laplacian is ignored and the corresponding output term of the potential is set to zero. Since
the Laplacian of the density is computable in Quantum ESPRESSO, they might be fully
exploited with a limited intervention on the code.

                                              18
```
