# 4.5 Understanding the time report

- Official source: https://www.quantum-espresso.org/Doc/pw_user_guide/node19.html
- Retrieved: 2026-07-17T11:51:11+00:00
- Official source SHA-256: `eb75ea6058991ef383fa1d78d12ed6e0f8b5c5acd5307825738850a13125f54b`
- Extracted text SHA-256: `19b307572e28ed0beb7341f215dfe5d9de99b2375d22701d75b307785719098b`
- Official Last-Modified: Mon, 08 Dec 2025 20:49:50 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.6 Restarting

Up:

4 Performances

Previous:

4.4 Parallelization issues

  

Contents

Subsections

4.5.1 Serial execution

4.5.2 Parallel execution

4.5.2.1 Quick estimate of parallelization parameters

4.5.2.2 Automatic guess of parallelization parameters

4.5.2.3 Typical symptoms of bad/inadequate parallelization

4.5 Understanding the time report

The time report printed at the end of a 
pw.x
run contains a lot of useful 
information that can be used to understand bottlenecks and improve 
performances.

4.5.1 Serial execution

The following applies to calculations taking a sizable amount of time
(at least minutes): for short calculations (seconds), the time spent in 
the various initializations dominates. Any discrepancy with the following
picture signals some anomaly.

For a typical job with norm-conserving PPs, the total (wall) time is mostly 
spent in routine "electrons", calculating the self-consistent solution. 

Most of the time spent in "electrons" is used by routine "c_bands", 
calculating Kohn-Sham states. "sum_band" (calculating the charge density),
"v_of_rho" (calculating the potential), "mix_rho" (charge density mixing)
should take a small fraction of the time.

Most of the time spent in "c_bands" is used by routines "cegterg" (k-points)
or "regterg" (Gamma-point only), performing iterative diagonalization of
the Kohn-Sham Hamiltonian in the PW basis set. 

Most of the time spent in "*egterg" is used by routine "h_psi",
calculating 
Hψ
products. "cdiaghg" (k-points) or "rdiaghg" (Gamma-only), 
performing subspace diagonalization, should take only a small fraction.

Among the "general routines", most of the time is spent in FFT on Kohn-Sham
states: "fftw", and to a smaller extent in other FFTs, "fft" and "ffts", 
and in "calbec", calculating 

〈
ψ
| 
β
〉 products. 

Forces and stresses typically take a fraction of the order of 10 to 20%
of the total time.

For PAW and Ultrasoft PP, you will see a larger contribution by "sum_band" 
and a nonnegligible "newd" contribution to the time spent in "electrons", 
but the overall picture is unchanged. You may drastically reduce the
overhead of Ultrasoft PPs by using input option "tqr=.true.".

4.5.2 Parallel execution

The various parallelization levels should be used wisely in order to 
achieve good results. Let us summarize the effects of them on CPU:

Parallelization on FFT speeds up (with varying efficiency) almost 
all routines, with the notable exception of "cdiaghg" and "rdiaghg".

Parallelization on k-points speeds up (almost linearly) "c_bands" and 
called routines; speeds up partially "sum_band"; does not speed up
at all "v_of_rho", "newd", "mix_rho".

Linear-algebra parallelization speeds up (not always) "cdiaghg"
and "rdiaghg".

"task-group" parallelization speeds up "fftw".

OpenMP parallelization speeds up "fftw", plus selected parts of the 
calculation, plus (depending on the availability of OpenMP-aware
libraries) some linear algebra operations.

and on RAM:

Parallelization on FFT distributes most arrays across processors
(i.e. all G-space and R-spaces arrays) but not all of them (in
particular, not subspace Hamiltonian and overlap matrices).

Linear-algebra parallelization also distributes subspace Hamiltonian
and overlap matrices.

All other parallelization levels do not distribute any memory.

In an ideally parallelized run, you should observe the following:

CPU and wall time do not differ by much, if OpenMP is not active, or:
CPU time approaches wall time times the number of OpenMP threads,
if OpenMP is active.

Time usage is still dominated by the same routines as for the serial run.

Routine "fft_scatter" (called by parallel FFT) takes a sizable part of
the time spent in FFTs but does not dominate it.

4.5.2.1 Quick estimate of parallelization parameters

You need to know

the number of k-points, 
N
k

the third dimension of the (smooth) FFT grid, 
N
3

the number of Kohn-Sham states, 
M

These data allow to set bounds on parallelization:

k-point parallelization is limited to 
N
k
processor pools: 

-nk Nk

FFT parallelization shouldn't exceed 
N
3
processors, i.e. if you
run with 
-nk Nk
, use 

N
= 
N
k
×
N
3
MPI processes at most (
mpirun -np N ...
)

Unless 
M
is a few hundreds or more, don't bother using linear-algebra
parallelization

You will need to experiment a bit to find the best compromise. In order
to have good load balancing among MPI processes, the number of k-point
pools should be an integer divisor of 
N
k
; the number of processors for
FFT parallelization should be an integer divisor of 
N
3
. 

4.5.2.2 Automatic guess of parallelization parameters

Since v.7.1, the code tries to guess a reasonable set of parameters
for the k-point, linear-algebra, and task-group parallelizations, if
they are not explicitly provided in the command line. The logic is
as follows:

if the number of processors 
N
p
exceeds 
N
3
, one uses k-point
parallelization on the smallest number 
N
k
such that

N
p
/
N
k
≤
N
3
/2;

if the number of processors 
N
p
/
N
k
still exceeds 
N
3
, one uses
task-group parallelization on the smallest 
N
t
that ensures

N
p
/
N
k
/
N
t
≤
N
3
/4;

linear-algebra parallelization is done on 
n
d
2
processors
(

n
d
2
≤
N
p
/
N
k
/
N
t
) with 
n
d
such that 

M
/
n
d
∼100.

4.5.2.3 Typical symptoms of bad/inadequate parallelization

a large fraction of time is spent in "v_of_rho", "newd", "mix_rho"
, or

the time doesn't scale well or doesn't scale at all by increasing the 
number of processors for k-point parallelization.
Solution:

use (also) FFT parallelization if possible

a disproportionate time is spent in "cdiaghg"/"rdiaghg".
Solutions:

use (also) k-point parallelization if possible

use linear-algebra parallelization, with scalapack if possible.

a disproportionate time is spent in "fft_scatter"
, or

in "fft_scatter" the difference between CPU and wall time is large.
Solutions:

if you do not have fast (better than Gigabit ethernet) communication
hardware, do not try FFT parallelization on more than 4 or 8 procs.

use (also) k-point parallelization if possible

the time doesn't scale well or doesn't scale at all by increasing the 
number of processors for FFT parallelization.

Solutions:

use "task groups": try command-line option 
-ntg 4
or

-ntg 8
. This may improve your scaling.

next 

up 

previous 

contents 

Next:

4.6 Restarting

Up:

4 Performances

Previous:

4.4 Parallelization issues

  

Contents
```
