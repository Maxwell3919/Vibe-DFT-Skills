# pw_user_guide.pdf — page 19

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `d9dcea0aa6eb24e943bd076ddfcfd16dcd751429c4e5db869661ad9eb3e9433c`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
        – use (also) k-point parallelization if possible
        – use linear-algebra parallelization, with scalapack if possible.

    a disproportionate time is spent in ”fft scatter”, or in ”fft scatter” the difference between
     CPU and wall time is large. Solutions:

        – if you do not have fast (better than Gigabit ethernet) communication hardware, do
          not try FFT parallelization on more than 4 or 8 procs.
        – use (also) k-point parallelization if possible

    the time doesn’t scale well or doesn’t scale at all by increasing the number of processors
     for FFT parallelization. Solutions:

        – use ”task groups”: try command-line option -ntg 4 or -ntg 8. This may improve
          your scaling.

4.6     Restarting
Since QE 5.1 restarting from an arbitrary point of the code is no more supported.
    The code must terminate properly in order for restart to be possible. A clean stop can be
triggered by one the following three conditions:

  1. The amount of time specified by the input variable max seconds is reached

  2. The user creates a file named ”$prefix.EXIT” either in the working directory or in output
     directory ”$outdir” (variables $outdir and $prefix as specified in the control namelist)

  3. (experimental) The code is compiled with signal-trapping support and one of the trapped
     signals is received (see the next section for details).

    After the condition is met, the code will try to stop cleanly as soon as possible, which can
take a while for large calculation. Writing the files to disk can also be a long process. In order
to be safe you need to reserve sufficient time for the stop process to complete.
    If the previous execution of the code has stopped properly, restarting is possible setting
restart mode=“restart” in the control namelist.

4.6.1   Signal trapping (experimental!)
In order to compile signal-trapping add ”-D TERMINATE GRACEFULLY” to DFLAGS in
the make.doc file. Currently the code intercepts SIGINT, SIGTERM, SIGUSR1, SIGUSR2,
SIGXCPU; signals can be added or removed editing the file clib/custom signals.c.
   Common queue systems will send a signal some time before killing a job. The exact be-
haviour depends on the queue systems and could be configured. Some examples:
   With PBS:

    send the default signal (SIGTERM) 120 seconds before the end:
     #PBS -l signal=@120

    send signal SIGUSR1 10 minutes before the end:
     #PBS -l signal=SIGUSR1@600

                                               19
```
