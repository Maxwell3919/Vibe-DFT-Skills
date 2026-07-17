# 3.6 Socket interface with i-PI

- Official source: https://www.quantum-espresso.org/Doc/pw_user_guide/node13.html
- Retrieved: 2026-07-17T11:50:59+00:00
- Official source SHA-256: `771dda1b6142b1079aad6cee2153eaa03f5cfd8ac90ea57d131473b32eed004d`
- Extracted text SHA-256: `a6bca3b9b13dee6e4e39b5ebc2c91ad29f506abd107ceb4e4272311985679e9f`
- Official Last-Modified: Mon, 08 Dec 2025 20:49:50 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4 Performances

Up:

3 Using PWscf

Previous:

3.5 Direct interface with CASINO

  

Contents

Subsections

3.6.0.1 Practicalities

3.6.0.2 How to use the i-PI inteface

3.6.0.3 Advanced i-PI usage

3.6 Socket interface with i-PI

The i-PI universal force engine performs advanced Molecular Dynamics
(MD) (such as Path Integral Molecular Dynamics, Thermodynamic
Integration, Suzuki-Chin path integral, Multiple Time Step molecular
dynamics) and other force related computations (see 
ipi-code.org

for more information about i-PI). 

PWscf
users wishing to learn how to use i-PI should refer to the i-PI website.

3.6.0.1 Practicalities

The communication between 
PWscf
and i-PI relies on a socket
interface. This allows running i-PI and 
PWscf
on different computers
provided that the two computers have an Internet
connection. Basically, i-PI works as a server waiting for a connection
of a suitable software (for example 
PWscf
). When this happens, i-PI
injects atomic positions and cell parameters into the software, that
will return forces and stress tensor to i-PI. 

The file containing the interface is 
run_driver.f90
. The files

socket.c
and 
fsocket.f90
provide the necessary
infrastructure to the socket interface. 

3.6.0.2 How to use the i-PI inteface

Since the communication goes through the Internet, the

PWscf
instance needs to know the address of the i-PI server that can
be specified with the command line option 
--ipi
(or

-ipi
) followed by the address of the computer running i-PI and
the port number where i-PI is listening, e.g. 

pw.x --ipi localhost:3142 -in pw.input > pw.out

If i-PI and 
PWscf
are running on the same machine, a UNIX socket is
preferable since allows faster communications, e.g. 

pw.x --ipi socketname:UNIX -in pw.input > pw.out

In the last case, 
UNIX
is a keyword that tells to 
PWscf
to
look for an UNIX socket connection instead of an INET one. More
extensive examples and tutorials can be found at 
ipi-code.org
. 

The 
PWscf
input file must contain all the information to
perform a single point calculation (
calculation = "scf"
) which
are also used to initialize the 
PWscf
run. Thus, it is important
that the 
PWscf
input contains atomic positions and cell parameters
which are as close as possible to those specified in the i-PI input. 

3.6.0.3 Advanced i-PI usage

For more advanced users, calculation flags can be changed 
on-the-fly by parsing a single binary-encoded integer to QE through 
the i-PI socket. That gives users the flexibility to define what 
properties to be calculated. For example, if only a single SCF cycle 
is needed, traditionally 
run_driver.f90
would be set to 
calculate not only the potential energy, but also forces, stresses 
and initialize g-vectors. With the binary-integer encoded flags, now
one can turn flags on and off as necessary to speed up their code flow.

The sequence of flags that is currently accepted is: SCF, 
forces, stresses, variable-cell and ensembles. The latter is only
available if QE has been compiled against BEEF-vdW XC. For a SCF and
forces-only calculation, that would corresponds to a 
11000

sequence, which has a 
24
decimal representation. The QE side
of the i-PI socket expects the equivalent-decimal
+1
; therefore, 
for a 
11000
calculation, the integer 
25
would have to be 
parsed to the 
driver_init
subroutine in 
run_driver.f90
. If
any number less-than or equal-to 
1
is parsed to QE, it falls back
to its standard i-PI mode.

Currently, the QE i-PI interface can only reside in
three different states: "NEEDINIT", "READY" or "HAVEDATA". Whenever 
the socket sends a "STATUS" message to QE, it responds back with its 
current status. A simple calculation sequence of events would be: (1) an
"STATUS" message is received, QE sends back "NEEDINIT", (2) an "INIT"
message is received, QE waits for three data packets, (i) an integer
that identifies the client on the other side of the socket, (ii) the flag-encoded integer
mentioned above, which can be used to change calculation 
settings, and (iii) an initialization string. QE then changes its status
to "READY". (3) The server sends a "POSDATA" message and QE then expects 
a sequence of variables depending on the calculation settings; the default 
being: a 3-by-3 matrix with cell and 3-by-3 marix with its inverse (if 

lmovecell
is 
.TRUE.
) and a (# of atoms)-by-3 position matrix. QE 
proceeds and computes all active properties (e.g. SCF, forces, stresses, 
etc.) and change its status to "HAVEDATA" and expects a (4) "GETFORCE"
message from the socket. Once it is received, (5) QE sends back (i) a
float with the potential energy, (ii) an integer with the total number of
atoms, (iii) a (# of atoms)-by-3 matrix with forces (if 
lforce
is

.TRUE.
), (iv) a 9-element-virial tensor (if 
lstres
is

.TRUE.
). QE goes back to "NEEDINIT" status. The other side of socket
should be able to compute new positions and cell coordinates (if 
lmovecell

is 
.TRUE.
) and start the cycle again from (1).

next 

up 

previous 

contents 

Next:

4 Performances

Up:

3 Using PWscf

Previous:

3.5 Direct interface with CASINO

  

Contents
```
