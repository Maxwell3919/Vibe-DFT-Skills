# pw_user_guide.pdf — page 20

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `37d64d08fc93fe805fe11c7b5954509b9edfa8db64958322b6f7e5ecf44a6ae3`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
     you cand also send a signal manually with qsig

     or send a signal and then stop:
      qdel -W 120 jobid
      will send SIGTERM, wait 2 minutes than force stop.

    With LoadLeveler (untested): the SIGXCPU signal will be sent when wall softlimit is
reached, it will then stop the job when hardlimit is reached. You can specify both limits as:
# @ wall clock limit = hardlimit,softlimit
e.g. you can give pw.x thirty minutes to stop using:
# @ wall clock limit = 5:00,4:30



5     Troubleshooting
pw.x says ’error while loading shared libraries’ or ’cannot open shared object file’
and does not start Possible reasons:

     If you are running on the same machines on which the code was compiled, this is a library
      configuration problem. The solution is machine-dependent. On Linux, find the path to
      the missing libraries; then either add it to file /etc/ld.so.conf and run ldconfig (must
      be done as root), or add it to variable LD LIBRARY PATH and export it. Another
      possibility is to load non-shared version of libraries (ending with .a) instead of shared
      ones (ending with .so).

     If you are not running on the same machines on which the code was compiled: you need
      either to have the same shared libraries installed on both machines, or to load statically all
      libraries (using appropriate configure or loader options). The same applies to Beowulf-
      style parallel machines: the needed shared libraries must be present on all PCs.

errors in examples with parallel execution If you get error messages in the exam-
ple scripts – i.e. not errors in the codes – on a parallel machine, such as e.g.: run exam-
ple: -n: command not found you may have forgotten to properly define PARA PREFIX and
PARA POSTFIX.

pw.x prints the first few lines and then nothing happens (parallel execution) If
the code looks like it is not reading from input, maybe it isn’t: the MPI libraries need to be
properly configured to accept input redirection. Use pw.x -i and the input file name (see
Sec.4.4), or inquire with your local computer wizard (if any). Since v.4.2, this is for sure the
reason if the code stops at Waiting for input....

pw.x stops with error while reading data There is an error in the input data, typically
a misspelled namelist variable, or an empty input file. Unfortunately with most compilers the
code often reports Error while reading XXX namelist and no further useful information. Here
are some more subtle sources of trouble:




                                                20
```
