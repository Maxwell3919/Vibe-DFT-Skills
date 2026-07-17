# 4.6 Restarting

- Official source: https://www.quantum-espresso.org/Doc/pw_user_guide/node20.html
- Retrieved: 2026-07-17T11:51:14+00:00
- Official source SHA-256: `c93ed2de367518454c4529cf0c6c8b9520e3a75b0527791a067f01ed52a7c121`
- Extracted text SHA-256: `06d08611b47266a832751fe973fe6b3e1f26e53fcc6da4236ea5ab769727c356`
- Official Last-Modified: Mon, 08 Dec 2025 20:49:50 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

5 Troubleshooting

Up:

4 Performances

Previous:

4.5 Understanding the time report

  

Contents

Subsections

4.6.1 Signal trapping (experimental!)

4.6 Restarting

Since QE 5.1 restarting from an arbitrary point of the code is no more supported.

The code must terminate properly in order for restart to be possible. A clean stop can be triggered by one the following three conditions:

The amount of time specified by the input variable max_seconds is reached

The user creates a file named "$prefix.EXIT" either in the working
directory or in output directory "$outdir" 
(variables $outdir and $prefix as specified in the control namelist)

(experimental) The code is compiled with signal-trapping support and one of the trapped signals is received (see the next section for details).

After the condition is met, the code will try to stop cleanly as soon as possible, which can take a while for large calculation. Writing the files to disk can also be a long process. In order to be safe you need to reserve sufficient time for the stop process to complete.

If the previous execution of the code has stopped properly, restarting is possible setting restart_mode=``restart'' in the control namelist.

4.6.1 Signal trapping (experimental!)

In order to compile signal-trapping add "-D__TERMINATE_GRACEFULLY" to DFLAGS in the make.doc file. Currently the code intercepts SIGINT, SIGTERM, SIGUSR1, SIGUSR2, SIGXCPU; signals can be added or removed editing the file 
clib/custom_signals.c
.

Common queue systems will send a signal some time before killing a job. The exact behaviour depends on the queue systems and could be configured. Some examples:

With PBS:

send the default signal (SIGTERM) 120 seconds before the end:

#PBS -l signal=@120

send signal SIGUSR1 10 minutes before the end:

#PBS -l signal=SIGUSR1@600

you cand also send a signal manually with qsig

or send a signal and then stop:

qdel -W 120 jobid

will send SIGTERM, wait 2 minutes than force stop.

With LoadLeveler (untested): the SIGXCPU signal will be sent when wall 
softlimit
is reached, it will then stop the job when 
hardlimit
is reached. You can specify both limits as:

# @ wall_clock_limit = hardlimit,softlimit

e.g. you can give pw.x thirty minutes to stop using:

# @ wall_clock_limit = 5:00,4:30

next 

up 

previous 

contents 

Next:

5 Troubleshooting

Up:

4 Performances

Previous:

4.5 Understanding the time report

  

Contents
```
