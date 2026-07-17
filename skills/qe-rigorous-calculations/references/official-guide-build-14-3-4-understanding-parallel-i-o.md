# 3.4 Understanding parallel I/O

- Official source: https://www.quantum-espresso.org/Doc/user_guide/node21.html
- Retrieved: 2026-07-17T11:50:34+00:00
- Official source SHA-256: `52285222489daec17d3f91e5886e0a7e4ad7abbcf78d8b09ca426d4c3c94e883`
- Extracted text SHA-256: `1916487273f192d53c7df3e2cd53bcb57cc8812229c68dcd2153bd5234e5853a`
- Official Last-Modified: Mon, 08 Dec 2025 20:50:48 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

3.5 Tricks and problems

Up:

3 Parallelism

Previous:

3.3 Parallelization levels

  

Contents

3.4 Understanding parallel I/O

In parallel execution, each processor has its own slice of data
(Kohn-Sham orbitals, charge density, etc), that have to be written
to temporary files during the calculation,
or to data files at the end of the calculation.
This can be done in two different ways:

``collected'': all slices are
collected by the code to a single processor
that writes them to disk, in a single file,
using a format that doesn't depend upon
the number of processors or their distribution.
This is the default since v.6.2 for final data.

``portable'': as above, but data can be
copied to and read from a different machines
(this is not guaranteed with Fortran binary files).
Requires compilation with 
-D__HDF5

preprocessing option and HDF5 libraries.

There is a third format, no longer used for final
data but used for scratch and restart files:

``distributed'': each processor
writes its own slice to disk in its internal
format to a different file.
The ``distributed'' format is fast and simple,
but the data so produced is readable only by
a job running on the same number of processors,
with the same type of parallelization, as the
job who wrote the data, and if all
files are on a file system that is visible to all
processors (i.e., you cannot use local scratch
directories: there is presently no way to ensure
that the distribution of processes across
processors will follow the same pattern
for different jobs).

The directory for data is specified in input variables

outdir
and 
prefix
(the former can be specified
as well in environment variable ESPRESSO_TMPDIR):

outdir/prefix.save
. A copy of pseudopotential files
is also written there. If some processor cannot access the
data directory, the pseudopotential files are read instead
from the pseudopotential directory specified in input data.
Unpredictable results may follow if those files
are not the same as those in the data directory!

IMPORTANT:

Avoid I/O to network-mounted disks (via NFS) as much as you can!
Ideally the scratch directory 
outdir
should be a modern
Parallel File System. If you do not have any, you can use local
scratch disks (i.e. each node is physically connected to a disk
and writes to it) but you may run into trouble anyway if you
need to access your files that are scattered in an unpredictable
way across disks residing on different nodes.

You can use input variable 
disk_io
to vary the
amount of I/O done by 
pw.x
. The default value is

disk_io='low'
, so the code will store wavefunctions
into RAM and not on disk during the calculation. Specify

disk_io='medium'
only if you have too many k-points
and you run into trouble with memory; choose 
disk_io='none'

if you do not need to keep final data files.

next 

up 

previous 

contents 

Next:

3.5 Tricks and problems

Up:

3 Parallelism

Previous:

3.3 Parallelization levels

  

Contents
```
