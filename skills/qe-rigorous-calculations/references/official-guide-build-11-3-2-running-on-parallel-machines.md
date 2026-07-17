# 3.2 Running on parallel machines

- Official source: https://www.quantum-espresso.org/Doc/user_guide/node19.html
- Retrieved: 2026-07-17T11:50:30+00:00
- Official source SHA-256: `e65b7dd14a8503f532bffa6de09ab478b8fc27dbaabee03508576d5732138266`
- Extracted text SHA-256: `cb552b338b2fe323a84a17728dadae03b16cd23168cd6522c576106c58a8f492`
- Official Last-Modified: Mon, 08 Dec 2025 20:50:48 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

3.3 Parallelization levels

Up:

3 Parallelism

Previous:

3.1 Understanding Parallelism

  

Contents

3.2 Running on parallel machines

Parallel execution is strongly system- and installation-dependent.
Typically one has to specify:

a launcher program such as 
mpirun
or 
mpiexec
,
with the appropriate options (if any);

the number of processors, typically as an option to the launcher
program;

the program to be executed, with the proper path if needed;

other Q
UANTUM 
ESPRESSO-specific parallelization options, to be
read and interpreted by the running code.

Items 1) and 2) are machine- and installation-dependent, and may be
different for interactive and batch execution. Note that large
parallel machines are often configured so as to disallow interactive
execution: if in doubt, ask your system administrator.
Item 3) also depend on your specific configuration (shell, execution path, etc).
Item 4) is optional but it is very important
for good performances. We refer to the next
section for a description of the various
possibilities.
```
