# 4.4 Parallelization issues

- Official source: https://www.quantum-espresso.org/Doc/pw_user_guide/node18.html
- Retrieved: 2026-07-17T11:51:09+00:00
- Official source SHA-256: `a0907e4d08f50bf90f6953f705fea6bfb8316fd9465e4671827691749d00a1cf`
- Extracted text SHA-256: `42c11925bd1f4625d337e6a089ddc0ce0e839ce29ffbb29b989e97aae81efffe`
- Official Last-Modified: Mon, 08 Dec 2025 20:49:50 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.5 Understanding the time report

Up:

4 Performances

Previous:

4.3 File space requirements

  

Contents

4.4 Parallelization issues

pw.x
can run in principle on any number of processors.
The effectiveness of parallelization is ultimately judged by the 
''scaling'', i.e. how the time needed to perform a job scales
with the number of processors, and depends upon:

the size and type of the system under study;

the judicious choice of the various levels of parallelization 
(detailed in Sec.
4.4
);

the availability of fast interprocess communications (or lack of it).

Ideally one would like to have linear scaling, i.e. 

T
∼
T
0
/
N
p
for 

N
p
processors, where 
T
0
is the estimated time for serial execution.
In addition, one would like to have linear scaling of
the RAM per processor: 

O
N
∼
O
0
/
N
p
, so that large-memory systems
fit into the RAM of each processor.

Parallelization on k-points:

guarantees (almost) linear scaling if the number of k-points
is a multiple of the number of pools;

requires little communications (suitable for ethernet communications);

reduces the required memory per processor by distributing wavefunctions
(but not other quantities like the charge density). Does not hold if you set 

disk_io='high'
.

Parallelization on PWs:

yields good to very good scaling, especially if the number of processors
in a pool is a divisor of 
N
3
and 
N
r3
(the dimensions along the z-axis 
of the FFT grids, 
nr3
and 
nr3s
, which coincide for NCPPs);

requires heavy communications (suitable for Gigabit ethernet up to 
4, 8 CPUs at most, specialized communication hardware needed for 8 or more
processors );

yields almost linear reduction of memory per processor with the number
of processors in the pool.

A note on scaling: optimal serial performances are achieved when the data are
as much as possible kept into the cache. As a side effect, PW
parallelization may yield superlinear (better than linear) scaling,
thanks to the increase in serial speed coming from the reduction of data size 
(making it easier for the machine to keep data in the cache).

VERY IMPORTANT: For each system there is an optimal range of number of processors on which to 
run the job. A too large number of processors will yield performance 
degradation. If the size of pools is especially delicate: 
N
p
should not 
exceed 
N
3
and 
N
r3
, and should ideally be no larger than

1/2÷1/4
N
3
and/or 
N
r3
. In order to increase scalability,
it is often convenient to 
further subdivide a pool of processors into ''task groups''.
When the number of processors exceeds the number of FFT planes, 
data can be redistributed to "task groups" so that each group 
can process several wavefunctions at the same time.

The optimal number of processors for "linear-algebra"
parallelization, taking care of multiplication and diagonalization 
of 
M
×
M
matrices, should be determined by observing the
performances of 
cdiagh/rdiagh
(
pw.x
) or 
ortho
(
cp.x
)
for different numbers of processors in the linear-algebra group
(must be a square integer).

Actual parallel performances will also depend on the available software 
(MPI libraries) and on the available communication hardware. For
PC clusters, OpenMPI (
http://www.openmpi.org/
) seems to yield better 
performances than other implementations (info by Kostantin Kudin). 
Note however that you need a decent communication hardware (at least 
Gigabit ethernet) in order to have acceptable performances with 
PW parallelization. Do not expect good scaling with cheap hardware: 
PW calculations are by no means an "embarrassing parallel" problem.

Also note that multiprocessor motherboards for Intel Pentium CPUs typically 
have just one memory bus for all processors. This dramatically
slows down any code doing massive access to memory (as most codes 
in the Q
UANTUM 
ESPRESSO distribution do) that runs on processors of the same
motherboard.

next 

up 

previous 

contents 

Next:

4.5 Understanding the time report

Up:

4 Performances

Previous:

4.3 File space requirements

  

Contents
```
