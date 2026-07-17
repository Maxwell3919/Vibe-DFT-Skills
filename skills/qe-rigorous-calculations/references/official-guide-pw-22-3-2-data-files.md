# 3.2 Data files

- Official source: https://www.quantum-espresso.org/Doc/pw_user_guide/node9.html
- Retrieved: 2026-07-17T11:51:30+00:00
- Official source SHA-256: `b14d84b5d31852296fe4d88c7139dc638db2ef6df769643e4766d4e372c47797`
- Extracted text SHA-256: `5e692ef6d5be97f66fa494ef2fd5e236dd3f55f98e5d1d907b3536f532fea4f2`
- Official Last-Modified: Mon, 08 Dec 2025 20:49:50 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

3.3 Electronic structure calculations

Up:

3 Using PWscf

Previous:

3.1 Input data

  

Contents

3.2 Data files

The output data files are written in the directory 
outdir/prefix.save
,
as specified in variable 
prefix
(a string that is prepended
to all file names, whose default value is 
prefix='pwscf'
).

outdir
is specified via environment variable

ESPRESSO_TMPDIR
. The usage of variable 
outdir
is
still possible but 
deprecated
. The 
FoX
library is used
to write a ``head'' data file in a XML format. This file has a ``schema''
that can be found on 
https://github.com/QEF/qeschemas
.

In case of multi-step calculations such as: 
'
md
'
, 
'
relax
'
, 

'
vc-md 
'
, 
'
vc-relax
'
the XML files contains also elements reporting the intermediate 
configurations. By default includes a maximum of 250 intermediate elements uniformly distributed along the trajectory 
and including first and last step. If one want to change the maximum number of intermediate steps described in the 
XML file it is sufficient to set the 
MAX_XML_STEPS
variable to the desired value. 

For more information about the XML file contents see the Developer Manual. The data directory contains
binary files that are not guaranteed to be readable on different machines.
If you need file portability, compile the code with HDF5 (see the general
User Guide).

The execution stops if you create an ``EXIT'' file 
prefix.EXIT
either
in the working directory (i.e. where the program is executed), or in
the 
outdir
directory. Note that with some versions of MPI,
the working directory is the directory where the executable is! 
The advantage of this procedure is that all files are properly closed, 
whereas just killing the process may leave data and output files in 
an unusable state. If you start the execution with the EXIT file already
in place, the code will stop after initialization. Alternatively:
set 
nstep
to 0 in input. This is useful to have
a quick check of the correctness of the input. 

next 

up 

previous 

contents 

Next:

3.3 Electronic structure calculations

Up:

3 Using PWscf

Previous:

3.1 Input data

  

Contents
```
